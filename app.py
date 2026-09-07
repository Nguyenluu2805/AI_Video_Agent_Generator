"""
AI Lecture Video Studio - Web Application Server
Flask RESTful API + SSE Real-time Streaming + Modern Dark SaaS Web UI
"""

import os
import sys
import json
import time
import queue
import threading
from pathlib import Path
from flask import Flask, render_template, request, jsonify, Response, send_from_directory
from werkzeug.utils import secure_filename

# Add src to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "src"))

import config
from extractor import run_extractor
from script_gen import run_script_generator
from voice_utils import extract_audio_from_media
from pipeline import run_full_pipeline

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB max upload

@app.after_request
def add_cache_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Thư mục lưu trữ
VOICE_SAMPLES_DIR = config.PROJECT_ROOT / "voice_samples"
VOICE_SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

# Trạng thái tiến trình toàn cục
log_queues = []
current_job = {
    "status": "idle",
    "progress": 0,
    "current_step": "",
    "log": [],
    "output_video": "",
    "error_message": ""
}

def broadcast_progress(step_name: str, progress_percent: int, log_line: str):
    """Phát tin nhắn tiến trình qua Server-Sent Events (SSE)."""
    current_job["current_step"] = step_name
    current_job["progress"] = progress_percent
    current_job["log"].append(log_line)

    msg = json.dumps({
        "step": step_name,
        "progress": progress_percent,
        "log": log_line,
        "status": current_job["status"],
        "video": current_job["output_video"]
    }, ensure_ascii=False)

    for q in list(log_queues):
        try:
            q.put_nowait(msg)
        except Exception:
            pass

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/upload", methods=["POST"])
def upload_file():
    """Tải lên file bài giảng .pptx."""
    if "file" not in request.files:
        return jsonify({"error": "Không tìm thấy file trong yêu cầu"}), 400

    file = request.files["file"]
    if not file.filename.lower().endswith(".pptx"):
        return jsonify({"error": "Định dạng file không hợp lệ! Vui lòng chỉ tải lên file .pptx"}), 400

    filename = secure_filename(file.filename) or "presentation.pptx"
    config.INPUT_DIR.mkdir(parents=True, exist_ok=True)
    save_path = config.INPUT_DIR / filename
    file.save(str(save_path.resolve()))

    return jsonify({
        "success": True,
        "filename": filename,
        "size_kb": round(save_path.stat().st_size / 1024, 1),
        "message": f"Tải lên thành công file: {filename}"
    })

@app.route("/api/upload-voice-sample", methods=["POST"])
def upload_voice_sample():
    """Tải lên file video hoặc audio để trích xuất giọng người thật."""
    if "file" not in request.files:
        return jsonify({"error": "Không tìm thấy file giọng mẫu"}), 400

    file = request.files["file"]
    filename = secure_filename(file.filename) or "voice_sample.mp4"
    temp_path = VOICE_SAMPLES_DIR / f"temp_{filename}"
    file.save(str(temp_path.resolve()))

    try:
        final_wav = extract_audio_from_media(temp_path)
        if temp_path.exists():
            temp_path.unlink()

        return jsonify({
            "success": True,
            "filename": filename,
            "size_mb": round(final_wav.stat().st_size / (1024 * 1024), 2),
            "message": "Trích xuất mẫu giọng chuẩn WAV thành công!"
        })
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        return jsonify({"error": f"Lỗi khi trích xuất âm thanh: {str(e)}"}), 500

@app.route("/api/extract-and-script", methods=["POST"])
def extract_and_script():
    """Trích xuất slide và sinh kịch bản phục vụ chỉnh sửa trước khi render."""
    data = request.json or {}
    filename = data.get("filename", "demo_lecture.pptx")
    gemini_key = data.get("gemini_api_key", "").strip()

    # Tìm file pptx
    pptx_path = config.INPUT_DIR / filename
    if not pptx_path.exists():
        pptx_path = config.PROJECT_ROOT / filename
    if not pptx_path.exists():
        pptx_path = config.PROJECT_ROOT / "demo_lecture.pptx"

    if not pptx_path.exists():
        return jsonify({"error": f"Không tìm thấy file bài giảng: {filename}"}), 404

    try:
        slides = run_extractor(pptx_path)
        scripts = run_script_generator(slides, gemini_api_key=gemini_key)

        result_slides = []
        for i, s in enumerate(slides, start=1):
            script_text = ""
            for item in scripts:
                if item["slide_index"] == i:
                    script_text = item["script"]
                    break

            result_slides.append({
                "slide_index": i,
                "title": s.get("title", f"Slide {i}"),
                "script": script_text,
                "image_url": f"/api/slide-image/slide_{i:03d}.png"
            })

        return jsonify({"success": True, "slides": result_slides})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/start-pipeline", methods=["POST"])
def start_pipeline():
    """Khởi động toàn bộ luồng tạo video 5 bước."""
    if current_job["status"] == "running":
        return jsonify({"error": "Tiến trình khác đang thực thi, vui lòng đợi hoàn tất!"}), 400

    data = request.json or {}
    filename = data.get("filename", "demo_lecture.pptx")
    custom_scripts = data.get("custom_scripts", None)
    gemini_key = data.get("gemini_api_key", "").strip()
    voice = data.get("voice", "vi-VN-NamMinhNeural")
    enable_rvc = bool(data.get("enable_rvc", False))

    pptx_path = config.INPUT_DIR / filename
    if not pptx_path.exists():
        pptx_path = config.PROJECT_ROOT / filename
    if not pptx_path.exists():
        pptx_path = config.PROJECT_ROOT / "demo_lecture.pptx"

    if not pptx_path.exists():
        return jsonify({"error": f"Không tìm thấy file bài giảng: {filename}"}), 404

    current_job["status"] = "running"
    current_job["progress"] = 0
    current_job["log"] = []
    current_job["error_message"] = ""
    current_job["output_video"] = ""

    def worker():
        try:
            out_video = run_full_pipeline(
                pptx_path=pptx_path,
                custom_scripts=custom_scripts,
                gemini_api_key=gemini_key,
                voice_name=voice,
                enable_rvc=enable_rvc,
                output_filename="output_video.mp4",
                on_progress=broadcast_progress
            )
            current_job["status"] = "completed"
            current_job["output_video"] = out_video.name
            broadcast_progress("Hoàn Thành", 100, f"Đã tạo video hoàn tất: {out_video.name}")
        except Exception as e:
            current_job["status"] = "error"
            current_job["error_message"] = str(e)
            broadcast_progress("Lỗi", 0, f"Lỗi xảy ra trong quá trình xử lý: {str(e)}")

    threading.Thread(target=worker, daemon=True).start()
    return jsonify({"success": True, "message": "Tiến trình tạo video đã được khởi động!"})

@app.route("/api/progress-stream")
def progress_stream():
    """SSE Stream gửi dữ liệu tiến trình thời gian thực về giao diện người dùng."""
    def event_stream():
        q = queue.Queue()
        log_queues.append(q)
        try:
            init_msg = json.dumps({
                "step": current_job["current_step"],
                "progress": current_job["progress"],
                "log": "Đã kết nối luồng trạng thái thời gian thực...",
                "status": current_job["status"],
                "video": current_job["output_video"]
            }, ensure_ascii=False)
            yield f"data: {init_msg}\n\n"

            while True:
                msg = q.get()
                yield f"data: {msg}\n\n"
        except GeneratorExit:
            if q in log_queues:
                log_queues.remove(q)

    return Response(event_stream(), mimetype="text/event-stream")

@app.route("/api/slide-image/<filename>")
def serve_slide_image(filename):
    return send_from_directory(str(config.IMAGES_DIR.resolve()), filename)

@app.route("/api/video/<filename>")
def serve_video(filename):
    return send_from_directory(str(config.OUTPUT_DIR.resolve()), filename, mimetype="video/mp4")

@app.route("/api/download-video/<filename>")
def download_video(filename):
    return send_from_directory(str(config.OUTPUT_DIR.resolve()), filename, as_attachment=True)

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 ĐANG KHỞI ĐỘNG MÁY CHỦ AI LECTURE STUDIO")
    print("👉 Mở trình duyệt tại địa chỉ: http://127.0.0.1:5000")
    print("=" * 60 + "\n")
    try:
        from waitress import serve
        serve(app, host="127.0.0.1", port=5000, threads=8)
    except Exception:
        app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
