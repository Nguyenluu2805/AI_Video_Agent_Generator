"""
Module: video_renderer.py
Description: Lắp ráp các slide ảnh 1080p và file audio thành video bài giảng hoàn chỉnh (.mp4).
"""

import os
import sys
import json
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Any

try:
    from . import config
except (ImportError, ValueError):
    import config

def get_audio_duration(audio_path: str) -> float:
    """Lấy thời lượng chính xác của file audio bằng FFmpeg."""
    import imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    cmd = [ffmpeg_exe, "-i", audio_path]
    result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, errors="ignore")
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", result.stderr)
    if match:
        hours = float(match.group(1))
        minutes = float(match.group(2))
        seconds = float(match.group(3))
        return hours * 3600 + minutes * 60 + seconds
    return 5.0


def assemble_video(slide_items: List[Dict[str, Any]], output_video_path: Path) -> Path:
    """Lắp ráp tất cả slide và audio thành video MP4 1080p bằng FFmpeg."""
    import imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    temp_clips = []
    temp_dir = config.WORKSPACE_DIR / "temp_clips"
    temp_dir.mkdir(parents=True, exist_ok=True)

    for i, item in enumerate(slide_items, start=1):
        img_path = item["image_path"]
        audio_path = item["audio_path"]
        duration = get_audio_duration(audio_path) + config.SLIDE_PAUSE_DURATION

        clip_path = temp_dir / f"clip_{i:03d}.mp4"
        temp_clips.append(clip_path)

        cmd = [
            ffmpeg_exe, "-y",
            "-loop", "1",
            "-i", img_path,
            "-i", audio_path,
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-vf", f"scale={config.VIDEO_WIDTH}:{config.VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={config.VIDEO_WIDTH}:{config.VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2",
            "-t", str(duration),
            "-shortest",
            str(clip_path.resolve())
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    concat_list_file = temp_dir / "concat_list.txt"
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for clip in temp_clips:
            f_path = str(clip.resolve()).replace("\\", "/")
            f.write(f"file '{f_path}'\n")

    concat_cmd = [
        ffmpeg_exe, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list_file.resolve()),
        "-c", "copy",
        str(output_video_path.resolve())
    ]
    subprocess.run(concat_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return output_video_path


def run_video_renderer(slide_items: List[Dict[str, Any]] = None, output_name: str = "output_video.mp4") -> Path:
    """Hàm thực thi chính cho Bước 5: Render Video Hoàn Chỉnh"""
    if slide_items is None:
        final_meta = config.WORKSPACE_DIR / "final_audio_meta.json"
        if not final_meta.exists():
            raise FileNotFoundError(f"Chưa có file {final_meta}. Vui lòng chạy các bước trước.")
        with open(final_meta, "r", encoding="utf-8") as f:
            slide_items = json.load(f)

    output_video_path = config.OUTPUT_DIR / output_name
    assemble_video(slide_items, output_video_path)
    return output_video_path

run_step5 = run_video_renderer
