import os
import sys
import json
import time
import urllib.request
import subprocess
from pathlib import Path
import soundfile as sf

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import config

def ensure_gpt_sovits_server():
    """Check if GPT-SoVITS server is alive, otherwise start it."""
    try:
        req = urllib.request.Request("http://127.0.0.1:9880/docs")
        with urllib.request.urlopen(req, timeout=2) as resp:
            if resp.status == 200:
                return True
    except Exception:
        pass
        
    print("[*] Đang khởi động máy chủ GPT-SoVITS trên cổng 9880...")
    engine_dir = config.PROJECT_ROOT / "gpt_sovits_engine"
    cmd = [
        sys.executable, "-u", "-X", "utf8", "api_v2.py",
        "-a", "127.0.0.1", "-p", "9880",
        "-c", "GPT_SoVITS/configs/tts_infer.yaml"
    ]
    subprocess.Popen(cmd, cwd=str(engine_dir.resolve()))
    
    # Wait for server to be ready
    for _ in range(30):
        time.sleep(2)
        try:
            req = urllib.request.Request("http://127.0.0.1:9880/docs")
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    print("[✓] Máy chủ GPT-SoVITS đã sẵn sàng!")
                    return True
        except Exception:
            pass
    return False

def synthesize_text_gpt_sovits(text: str, output_mp3: Path, ref_wav: str, ref_text: str, speed: float = 1.0) -> float:
    """Synthesize speech using GPT-SoVITS /tts API and save as MP3."""
    temp_wav = output_mp3.with_suffix(".wav")
    payload = {
        "text": text,
        "text_lang": "en",
        "ref_audio_path": ref_wav,
        "prompt_text": ref_text,
        "prompt_lang": "en",
        "text_split_method": "cut5",
        "batch_size": 1,
        "speed_factor": speed,
        "media_type": "wav",
        "streaming_mode": 0
    }
    req = urllib.request.Request(
        "http://127.0.0.1:9880/tts",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        temp_wav.write_bytes(resp.read())
        
    # Convert WAV to high quality MP3
    subprocess.run([
        "ffmpeg", "-y", "-i", str(temp_wav.resolve()),
        "-c:a", "libmp3lame", "-b:a", "192k",
        str(output_mp3.resolve())
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    info = sf.info(str(temp_wav.resolve()))
    dur = info.duration
    
    if temp_wav.exists():
        try: temp_wav.unlink()
        except Exception: pass
        
    return dur

def run_gpt_sovits_cloning(scripts: list = None, speed: float = 1.0) -> list:
    """
    Generate authentic neural speech for all slides using GPT-SoVITS.
    """
    print(f"\n=======================================================")
    print(f"[GPT-SoVITS] Neural Voice Synthesis trên RTX 3060 Ti")
    print(f"=======================================================")
    
    ensure_gpt_sovits_server()
    config.FINAL_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    
    if scripts is None:
        script_file = config.WORKSPACE_DIR / "script.json"
        if not script_file.exists():
            raise FileNotFoundError(f"Chưa có file {script_file}. Vui lòng chạy Bước 2 trước.")
        with open(script_file, "r", encoding="utf-8") as f:
            scripts = json.load(f)
            
    voice_sample_dir = config.PROJECT_ROOT / "voice_samples"
    ref_wav = str((voice_sample_dir / "ref_sample.wav").resolve())
    with open(voice_sample_dir / "ref_sample.txt", "r", encoding="utf-8") as f:
        ref_text = f.read().strip()
        
    print(f"[*] Mẫu giọng tham chiếu: {Path(ref_wav).name}")
    print(f"[*] Văn bản tham chiếu: \"{ref_text}\"")
    
    final_records = []
    for item in scripts:
        idx = item["slide_index"]
        dst_audio = config.FINAL_AUDIO_DIR / f"final_slide_{idx:03d}.mp3"
        print(f"[*] Slide {idx}/{len(scripts)}: \"{item.get('title', '')}\"...")
        start_t = time.time()
        
        dur = synthesize_text_gpt_sovits(item["script"], dst_audio, ref_wav, ref_text, speed=speed)
        elapsed = round(time.time() - start_t, 1)
        print(f"    -> [✓] Đã tạo xong bằng GPT-SoVITS: {dst_audio.name} ({round(dur, 1)}s audio trong {elapsed}s GPU)")
        
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
        
    print(f"\n[✓] Hoàn thành sinh giọng GPT-SoVITS cho toàn bộ {len(final_records)} slide!")
    return final_records

if __name__ == "__main__":
    run_gpt_sovits_cloning()
