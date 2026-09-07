"""
Module: pipeline.py
Description: Quản lý và điều phối toàn bộ luồng 5 bước tự động hóa chuyển PPTX thành Video.
"""

import os
import sys
import time
from pathlib import Path
from typing import Callable, Optional, Dict, Any

try:
    from . import config
    from .extractor import run_extractor
    from .script_gen import run_script_generator
    from .tts_engine import run_tts_engine
    from .voice_cloner import run_voice_cloner
    from .video_renderer import run_video_renderer
except (ImportError, ValueError):
    import config
    from extractor import run_extractor
    from script_gen import run_script_generator
    from tts_engine import run_tts_engine
    from voice_cloner import run_voice_cloner
    from video_renderer import run_video_renderer

def run_full_pipeline(
    pptx_path: Path,
    custom_scripts: Optional[list] = None,
    gemini_api_key: Optional[str] = None,
    voice_name: Optional[str] = None,
    enable_rvc: bool = False,
    output_filename: str = "output_video.mp4",
    on_progress: Optional[Callable[[str, int, str], None]] = None
) -> Path:
    """Thực thi quy trình 5 bước hoàn chỉnh từ PPTX đến Video MP4."""
    def log(step: str, pct: int, msg: str):
        if on_progress:
            on_progress(step, pct, msg)
        print(f"[{pct}%] [{step}] {msg}")

    # Bước 1
    log("Bước 1: Trích xuất Slide", 10, f"Đang đọc file PowerPoint: {pptx_path.name}...")
    slides_data = run_extractor(pptx_path)
    log("Bước 1: Trích xuất Slide", 25, f"Đã xuất thành công {len(slides_data)} trang slide độ phân giải 1080p.")

    # Bước 2
    log("Bước 2: Tạo Kịch Bản", 30, "Đang khởi tạo lời giảng sư phạm cho từng slide...")
    if custom_scripts:
        scripts = custom_scripts
        log("Bước 2: Tạo Kịch Bản", 45, f"Đã nạp {len(scripts)} kịch bản tùy chỉnh của bạn.")
    else:
        scripts = run_script_generator(slides_data, gemini_api_key=gemini_api_key)
        log("Bước 2: Tạo Kịch Bản", 45, f"AI đã hoàn thành kịch bản sư phạm cho {len(scripts)} slide.")

    # Bước 3
    log("Bước 3: Tổng Hợp Giọng Nói", 50, f"Đang tổng hợp audio bằng giọng đọc: {voice_name or config.TTS_VOICE} (Xử lý song song)...")
    base_audio = run_tts_engine(scripts, voice_name=voice_name, on_progress=on_progress)
    log("Bước 3: Tổng Hợp Giọng Nói", 70, f"Đã tạo hoàn chỉnh {len(base_audio)} file âm thanh lồng tiếng.")

    # Bước 4
    log("Bước 4: Chuyển Đổi Âm Sắc", 75, "Đang xử lý Voice Cloning / Tối ưu âm thanh...")
    final_audio = run_voice_cloner(base_audio, enable_rvc=enable_rvc)
    log("Bước 4: Chuyển Đổi Âm Sắc", 85, "Âm thanh đã sẵn sàng cho bước ghép video.")

    # Bước 5
    log("Bước 5: Render Video 1080p", 90, f"Đang xuất video bài giảng cuối cùng ({output_filename})...")
    output_video = run_video_renderer(final_audio, output_name=output_filename)
    log("Hoàn Thành", 100, f"Video bài giảng đã được render thành công: {output_video.name}")

    return output_video
