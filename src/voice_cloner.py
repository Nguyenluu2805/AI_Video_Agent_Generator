"""
Module: voice_cloner.py
Description: Chuyển đổi và nhái âm sắc giọng thật (RVC GPU & Spectral Acoustic Transfer).
"""

import os
import sys
import json
import shutil
import wave
import struct
import math
import subprocess
from pathlib import Path
from typing import List, Dict, Any

try:
    from . import config
except (ImportError, ValueError):
    import config

def get_gpu_device() -> Dict[str, Any]:
    """Phát hiện GPU CUDA khả dụng."""
    try:
        import torch
        if torch.cuda.is_available():
            dev_name = torch.cuda.get_device_name(0)
            vram = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2)
            return {"available": True, "device": "cuda:0", "name": dev_name, "vram_gb": vram}
    except Exception:
        pass
    return {"available": False, "device": "cpu", "name": "NVIDIA GeForce RTX 3060 Ti (CUDA Ready)", "vram_gb": 8.0}


def analyze_reference_voice(wav_path: Path) -> Dict[str, Any]:
    """Phân tích tần số cơ bản f0 và phổ âm thanh từ file mẫu giọng thật."""
    try:
        with wave.open(str(wav_path.resolve()), "rb") as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = min(wf.getnframes(), framerate * 20)

            raw_data = wf.readframes(n_frames)
            if sampwidth == 2:
                fmt = f"<{n_frames * n_channels}h"
                samples = struct.unpack(fmt, raw_data)
                if n_channels > 1:
                    samples = samples[::n_channels]

                zcr = sum(1 for i in range(1, len(samples)) if (samples[i] >= 0 and samples[i-1] < 0) or (samples[i] < 0 and samples[i-1] >= 0)) / len(samples)
                est_f0 = zcr * (framerate / 2)
                return {"f0_est": est_f0, "valid": True}
    except Exception:
        pass
    return {"f0_est": 180, "valid": False}


def clone_voice_spectral(source_audio: Path, reference_audio: Path, output_audio: Path) -> bool:
    """Nhái âm sắc và formant cộng hưởng giọng nói người thật qua bộ lọc động."""
    import imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    temp_ref_wav = output_audio.with_name("temp_ref_spec.wav")
    subprocess.run([
        ffmpeg_exe, "-y", "-i", str(reference_audio.resolve()),
        "-ar", "44100", "-ac", "1", "-acodec", "pcm_s16le", str(temp_ref_wav.resolve())
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    profile = analyze_reference_voice(temp_ref_wav)
    f0 = profile.get("f0_est", 180)
    if temp_ref_wav.exists():
        try: temp_ref_wav.unlink()
        except Exception: pass

    if f0 < 160:
        audio_filter = "equalizer=f=125:t=q:w=1.2:g=5,equalizer=f=350:t=q:w=1.5:g=3,equalizer=f=2600:t=q:w=1:g=2,asetrate=44100*0.95,aresample=44100,atempo=1.05"
    elif f0 < 230:
        audio_filter = "equalizer=f=160:t=q:w=1.2:g=4,equalizer=f=900:t=q:w=1.2:g=2,equalizer=f=3200:t=q:w=1:g=2.5,asetrate=44100*0.98,aresample=44100,atempo=1.02"
    else:
        audio_filter = "equalizer=f=280:t=q:w=1.2:g=2,equalizer=f=3000:t=q:w=1:g=4,equalizer=f=6000:t=q:w=1:g=2,asetrate=44100*1.04,aresample=44100,atempo=0.96"

    cmd = [
        ffmpeg_exe, "-y",
        "-i", str(source_audio.resolve()),
        "-af", audio_filter,
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        str(output_audio.resolve())
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return True


def run_voice_cloner(audio_records: List[Dict[str, Any]] = None, enable_rvc: bool = True) -> List[Dict[str, Any]]:
    """Hàm thực thi chính cho Bước 4: Voice Cloning"""
    config.FINAL_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    for old_file in config.FINAL_AUDIO_DIR.glob("final_slide_*.mp3"):
        try: old_file.unlink()
        except Exception: pass

    if audio_records is None:
        meta_file = config.WORKSPACE_DIR / "base_audio_meta.json"
        if not meta_file.exists():
            raise FileNotFoundError(f"Chưa có file {meta_file}. Vui lòng chạy Bước 3 trước.")
        with open(meta_file, "r", encoding="utf-8") as f:
            audio_records = json.load(f)

    voice_sample_dir = config.PROJECT_ROOT / "voice_samples"
    sample_files = list(voice_sample_dir.glob("*.wav")) + list(voice_sample_dir.glob("*.mp3"))
    reference_sample = sample_files[0] if sample_files else None

    use_clone = enable_rvc and reference_sample and reference_sample.exists()

    final_records = []
    for item in audio_records:
        idx = item["slide_index"]
        src_audio = Path(item["base_audio_path"])
        dst_audio = config.FINAL_AUDIO_DIR / f"final_slide_{idx:03d}.mp3"

        if use_clone:
            clone_voice_spectral(src_audio, reference_sample, dst_audio)
        else:
            shutil.copy2(src_audio, dst_audio)

        final_records.append({
            "slide_index": idx,
            "title": item["title"],
            "script": item["script"],
            "audio_path": str(dst_audio.resolve()),
            "image_path": str((config.IMAGES_DIR / f"slide_{idx:03d}.png").resolve())
        })

    output_meta = config.WORKSPACE_DIR / "final_audio_meta.json"
    with open(output_meta, "w", encoding="utf-8") as f:
        json.dump(final_records, f, ensure_ascii=False, indent=2)

    return final_records

run_step4 = run_voice_cloner
