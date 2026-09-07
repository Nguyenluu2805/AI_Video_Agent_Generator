import os
import sys
import json
import time
import queue
import threading
from pathlib import Path
from flask import Flask, render_template, request, jsonify, Response, send_from_directory, send_file
from werkzeug.utils import secure_filename

# Add src to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "src"))

import config
from step1_extractor import run_step1
from step2_llm import run_step2
from step3_tts import run_step3
from step4_rvc import run_step4
from step5_video import run_step5
from extract_voice_sample import extract_audio_from_video

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB max upload

VOICE_SAMPLES_DIR = BASE_DIR / "voice_samples"
VOICE_SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

# Global progress queue for SSE
log_queues = []
current_job = {
    "status": "idle",
    "progress": 0,
    "current_step": "",
    "log": [],
    "output_video": "",
    "error_message": ""
}

def broadcast_log(step_name: str, progress_percent: int, log_line: str):
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
    gpu_name = "NVIDIA GeForce RTX 3060 Ti (8GB)"
    sample_wav = VOICE_SAMPLES_DIR / "my_voice_sample.wav"
    has_sample = sample_wav.exists()
    has_model = Path(config.RVC_MODEL_PATH).exists()
    
    return render_template("index.html", 
                           gemini_key_set=bool(config.GEMINI_API_KEY),
                           default_voice=config.TTS_VOICE,
                           gpu_name=gpu_name,
                           has_voice_sample=has_sample,
                           has_voice_model=has_model)

@app.route("/api/system-status")
def system_status():
    sample_wav = VOICE_SAMPLES_DIR / "my_voice_sample.wav"
    has_model = Path(config.RVC_MODEL_PATH).exists()
    return jsonify({
        "gpu": "NVIDIA GeForce RTX 3060 Ti (8GB)",
        "cuda_ready": True,
        "office_installed": True,
        "gemini_ready": bool(config.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")),
        "default_voice": config.TTS_VOICE,
        "has_voice_sample": sample_wav.exists(),
        "has_voice_model": has_model
    })

@app.route("/api/upload", methods=["POST"])
def upload_pptx():
    if "file" not in request.files:
        return jsonify({"error": "Không tìm thấy file tải lên"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Chưa chọn file"}), 400
        
    filename = secure_filename(file.filename)
    if not filename.lower().endswith(".pptx"):
        return jsonify({"error": "Định dạng file phải là PowerPoint (.pptx)"}), 400
        
    save_path = config.INPUT_DIR / filename
    file.save(str(save_path))
    return jsonify({
        "success": True,
        "filename": filename,
        "filepath": str(save_path.resolve()),
        "size_kb": round(save_path.stat().st_size / 1024, 1)
    })

@app.route("/api/upload-voice-sample", methods=["POST"])
def upload_voice_sample():
    if "file" not in request.files:
        return jsonify({"error": "Không tìm thấy file"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Chưa chọn file"}), 400
        
    filename = secure_filename(file.filename)
    save_path = VOICE_SAMPLES_DIR / filename
    file.save(str(save_path))
    
    wav_path = VOICE_SAMPLES_DIR / "my_voice_sample.wav"
    try:
        extract_audio_from_video(save_path, wav_path)
        size_mb = round(wav_path.stat().st_size / (1024*1024), 2)
        return jsonify({
            "success": True,
            "filename": filename,
            "wav_name": "my_voice_sample.wav",
            "size_mb": size_mb,
            "message": "Đã trích xuất và chuẩn hóa giọng nói của bạn thành công!"
        })
    except Exception as e:
        return jsonify({"error": f"Lỗi khi trích xuất giọng: {str(e)}"}), 500

@app.route("/api/extract-and-script", methods=["POST"])
def extract_and_script():
    data = request.get_json() or {}
    filename = data.get("filename", "")
    api_key = data.get("gemini_api_key", "").strip()
    
    if api_key:
        config.GEMINI_API_KEY = api_key
        
    pptx_path = config.INPUT_DIR / filename if filename else (config.INPUT_DIR / "demo_lecture.pptx")
    if not pptx_path.exists():
        # Check any pptx
        pptxs = list(config.INPUT_DIR.glob("*.pptx"))
        if pptxs:
            pptx_path = pptxs[0]
        else:
            return jsonify({"error": f"Không tìm thấy file slide nào trong input/"}), 404
        
    try:
        slides_data = run_step1(pptx_path)
        scripts = run_step2(slides_data)
        
        result = []
        for s in scripts:
            idx = s["slide_index"]
            result.append({
                "slide_index": idx,
                "title": s.get("title", f"Slide {idx}"),
                "script": s.get("script", ""),
                "image_url": f"/api/slide-image/slide_{idx:03d}.png"
            })
            
        return jsonify({"success": True, "slides": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/start-pipeline", methods=["POST"])
def start_pipeline():
    if current_job["status"] == "processing":
        return jsonify({"error": "Đang có một tiến trình tạo video khác đang chạy!"}), 400
        
    data = request.get_json() or {}
    filename = data.get("filename", "")
    custom_scripts = data.get("custom_scripts", None)
    enable_rvc = data.get("enable_rvc", False)
    voice = data.get("voice", "vi-VN-NamMinhNeural")
    gemini_key = data.get("gemini_api_key", "").strip()
    
    if gemini_key:
        config.GEMINI_API_KEY = gemini_key
    if voice:
        config.TTS_VOICE = voice
        
    pptx_path = config.INPUT_DIR / filename if filename else None
    if pptx_path is None or not pptx_path.exists():
        pptxs = list(config.INPUT_DIR.glob("*.pptx"))
        if pptxs:
            pptx_path = pptxs[0]
        else:
            pptx_path = config.INPUT_DIR / "demo_lecture.pptx"
            
    if not pptx_path.exists():
        return jsonify({"error": f"Không tìm thấy file PowerPoint để xử lý."}), 404
        
    current_job["status"] = "processing"
    current_job["progress"] = 0
    current_job["current_step"] = "Khởi động Pipeline"
    current_job["log"] = []
    current_job["output_video"] = ""
    current_job["error_message"] = ""
    
    selected_voice = voice
    
    def worker():
        try:
            broadcast_log("Bước 1/5: Trích xuất Slide PPTX", 10, f"Đang trích xuất hình ảnh 1080p và ghi chú từ {pptx_path.name}...")
            slides_data = run_step1(pptx_path)
            broadcast_log("Bước 1/5: Trích xuất Slide PPTX", 25, f"Đã xuất thành công {len(slides_data)} trang slide.")
            
            if custom_scripts and len(custom_scripts) > 0:
                broadcast_log("Bước 2/5: Kịch Bản Giảng Dạy", 40, "Sử dụng kịch bản đã được bạn duyệt/chỉnh sửa...")
                scripts = custom_scripts
                with open(config.WORKSPACE_DIR / "script.json", "w", encoding="utf-8") as f:
                    json.dump(scripts, f, ensure_ascii=False, indent=2)
            else:
                broadcast_log("Bước 2/5: Kịch Bản Giảng Dạy", 35, "AI đang viết bài giảng sư phạm chuyên sâu cho từng trang slide...")
                scripts = run_step2(slides_data)
                broadcast_log("Bước 2/5: Kịch Bản Giảng Dạy", 50, f"AI đã hoàn thành bài giảng cho {len(scripts)} slide.")
                
            voice_label = "GIỌNG NAM (Nam Minh)" if "nam" in selected_voice.lower() else "GIỌNG NỮ (Hoài My)"
            broadcast_log("Bước 3/5: Sinh Giọng Đọc (TTS)", 60, f"Đang tạo âm thanh {voice_label}...")
            base_audio = run_step3(scripts, voice_name=selected_voice)
            broadcast_log("Bước 3/5: Sinh Giọng Đọc (TTS)", 75, f"Đã tạo xong {len(base_audio)} file âm thanh.")
            
            broadcast_log("Bước 4/5: Voice Cloning (RVC)", 80, "Xử lý chuyển đổi âm sắc sang giọng của bạn qua GPU RTX 3060 Ti...")
            final_records = run_step4(base_audio, enable_rvc=enable_rvc)
            broadcast_log("Bước 4/5: Voice Cloning (RVC)", 85, "Âm thanh lồng tiếng đã sẵn sàng.")
            
            out_name = f"lecture_{int(time.time())}.mp4"
            broadcast_log("Bước 5/5: Lắp Ráp Video (.mp4)", 90, "Đang kết nối hình ảnh và âm thanh thành video Full HD...")
            out_path = run_step5(final_records, output_name=out_name)
            
            current_job["output_video"] = out_name
            current_job["status"] = "completed"
            broadcast_log("Hoàn Tất", 100, f"Video bài giảng đã tạo thành công: {out_name}!")
        except Exception as e:
            current_job["status"] = "error"
            current_job["error_message"] = str(e)
            broadcast_log("Lỗi", 0, f"Lỗi xảy ra trong quá trình xử lý: {str(e)}")
            
    threading.Thread(target=worker, daemon=True).start()
    return jsonify({"success": True, "message": "Tiến trình tạo video đã được khởi động!"})

@app.route("/api/progress-stream")
def progress_stream():
    def event_stream():
        q = queue.Queue()
        log_queues.append(q)
        try:
            init_msg = json.dumps({
                "step": current_job["current_step"],
                "progress": current_job["progress"],
                "log": "Kết nối luồng trạng thái thời gian thực...",
                "status": current_job["status"],
                "video": current_job["output_video"]
            }, ensure_ascii=False)
            yield f"data: {init_msg}\n\n"
            
            while True:
                msg = q.get()
                yield f"data: {msg}\n\n"
        except GeneratorExit:
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
    print("\n" + "="*60)
    print("🚀 ĐANG KHỞI ĐỘNG GIAO DIỆN WEB AI VIDEO AGENT")
    print("👉 Mở trình duyệt tại địa chỉ: http://127.0.0.1:5000")
    print("="*60 + "\n")
    try:
        from waitress import serve
        serve(app, host="127.0.0.1", port=5000, threads=8)
    except Exception:
        app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
