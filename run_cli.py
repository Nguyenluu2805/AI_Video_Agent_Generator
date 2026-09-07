"""
AI Video Agent Studio - Command Line Interface (CLI)
Sử dụng: python run_cli.py --input input/demo_lecture.pptx --voice vi-VN-NamMinhNeural
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import config
from pipeline import run_full_pipeline

def main():
    parser = argparse.ArgumentParser(description="AI Lecture Video Studio - CLI Pipeline Runner")
    parser.add_argument("--input", "-i", type=str, default="", help="Đường dẫn file bài giảng PowerPoint (.pptx)")
    parser.add_argument("--voice", "-v", type=str, default="", help="Mã giọng đọc TTS (vi-VN-NamMinhNeural, vi-VN-HoaiMyNeural, v.v.)")
    parser.add_argument("--enable-rvc", action="store_true", help="Kích hoạt Voice Cloning RVC trên GPU")
    parser.add_argument("--gemini-key", type=str, default="", help="API Key Google Gemini")
    parser.add_argument("--output", "-o", type=str, default="output_video.mp4", help="Tên file video đầu ra (.mp4)")

    args = parser.parse_args()

    pptx_path = None
    if args.input:
        pptx_path = Path(args.input)
    else:
        default_pptx = BASE_DIR / "demo_lecture.pptx" if 'BASE_DIR' in globals() else Path("demo_lecture.pptx")
        if default_pptx.exists():
            pptx_path = default_pptx
        else:
            candidates = list(Path("input").glob("*.pptx")) if Path("input").exists() else []
            if candidates:
                pptx_path = candidates[0]

    if not pptx_path or not pptx_path.exists():
        print(f"[!] Lỗi: Không tìm thấy file bài giảng .pptx. Vui lòng chỉ định: python run_cli.py --input path/to/slide.pptx")
        sys.exit(1)

    print("=" * 60)
    print("🎬 KHỞI ĐỘNG AI LECTURE STUDIO PIPELINE")
    print(f"👉 File Slide: {pptx_path.name}")
    print(f"👉 Giọng đọc: {args.voice or config.TTS_VOICE}")
    print(f"👉 Voice Cloning: {'BẬT' if args.enable_rvc else 'TẮT'}")
    print("=" * 60)

    output = run_full_pipeline(
        pptx_path=pptx_path,
        gemini_api_key=args.gemini_key,
        voice_name=args.voice,
        enable_rvc=args.enable_rvc,
        output_filename=args.output
    )

    print(f"\n🎉 HOÀN THÀNH: {output.resolve()}")

if __name__ == "__main__":
    main()
