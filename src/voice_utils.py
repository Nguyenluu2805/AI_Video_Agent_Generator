"""
Module: voice_utils.py
Description: Tiện ích trích xuất và xử lý âm thanh từ video bài giảng hoặc file ghi âm.
"""

import os
import sys
import subprocess
from pathlib import Path
import imageio_ffmpeg

try:
    from . import config
except (ImportError, ValueError):
    import config

def extract_audio_from_media(media_path: Path, output_wav: Path = None) -> Path:
    """Trích xuất file WAV mono 44.1kHz chuẩn từ video (.mp4, .mov) hoặc audio."""
    if output_wav is None:
        output_wav = config.PROJECT_ROOT / "voice_samples" / "my_voice_sample.wav"

    output_wav.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    cmd = [
        ffmpeg_exe, "-y",
        "-i", str(media_path.resolve()),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        "-ac", "1",
        str(output_wav.resolve())
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return output_wav

extract_audio_from_video = extract_audio_from_media
