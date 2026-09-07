import os
import sys
import json
import time
import subprocess
from pathlib import Path
import soundfile as sf
import torch

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import config

_F5_INSTANCE = None

def get_f5_cloner():
    """Singleton getter for F5TTS instance on CUDA."""
    global _F5_INSTANCE
    if _F5_INSTANCE is not None:
        return _F5_INSTANCE
        
    from f5_tts.api import F5TTS
    
    f5_dir = config.PROJECT_ROOT / "models" / "f5_tts"
    ckpt_file = f5_dir / "model_1250000.safetensors"
    vocab_file = f5_dir / "vocab.txt"
    vocos_dir = f5_dir / "vocos"
    
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print(f"[*] Khởi động F5-TTS Engine trên thiết bị: {device}...")
    
    _F5_INSTANCE = F5TTS(
        model="F5TTS_v1_Base",
        device=device
    )
    print(f"[✓] F5-TTS Engine đã sẵn sàng trong VRAM GPU!")
    return _F5_INSTANCE

def ensure_reference_sample() -> tuple:
    """
    Ensure a clean 6-10 second reference audio and transcript exist.
    """
    voice_sample_dir = config.PROJECT_ROOT / "voice_samples"
    ref_wav = voice_sample_dir / "ref_sample.wav"
    ref_txt = voice_sample_dir / "ref_sample.txt"
    
    if ref_wav.exists() and ref_txt.exists() and ref_txt.stat().st_size > 5:
        with open(ref_txt, "r", encoding="utf-8") as f:
            return str(ref_wav.resolve()), f.read().strip()
            
    # If not yet extracted, extract from my_voice_sample.wav
    source_sample = voice_sample_dir / "my_voice_sample.wav"
    if not source_sample.exists():
        samples = list(voice_sample_dir.glob("*.wav")) + list(voice_sample_dir.glob("*.mp3"))
        if samples:
            source_sample = samples[0]
        else:
            raise FileNotFoundError("Chưa có file mẫu giọng nói nào trong voice_samples/")
            
    cmd = [
        "ffmpeg", "-y", "-ss", "00:00:15", "-t", "8",
        "-i", str(source_sample.resolve()),
        "-ar", "24000", "-ac", "1",
        str(ref_wav.resolve())
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Transcribe with Gemini
    api_key = config.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            with open(ref_wav, "rb") as f:
                audio_bytes = f.read()
            prompt = "Hãy nghe đoạn âm thanh này và gõ lại CHÍNH XÁC từng từ tiếng Việt/tiếng Anh mà người nói đang nói (không thêm bớt bất kỳ từ nào, chỉ trả về đúng câu nói)."
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=[
                    prompt,
                    genai.types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav")
                ]
            )
            ref_text = response.text.strip()
            with open(ref_txt, "w", encoding="utf-8") as f:
                f.write(ref_text)
            return str(ref_wav.resolve()), ref_text
        except Exception:
            pass
            
    # Default fallback transcript if offline
    default_text = "Hôm nay chúng ta sẽ học bài Kiến trúc MCP Model Context Protocol. Ở session 12 này chúng ta sẽ có 4 lesson. Lesson 1"
    with open(ref_txt, "w", encoding="utf-8") as f:
        f.write(default_text)
    return str(ref_wav.resolve()), default_text

def run_f5_voice_cloning(scripts: list = None, speed: float = 1.0) -> list:
    """
    Generate authentic neural speech directly with F5-TTS for all lecture slides.
    """
    print(f"\n=======================================================")
    print(f"[Bước 3+4/5] F5-TTS Zero-Shot Voice Synthesis trên RTX 3060 Ti")
    print(f"=======================================================")
    
    config.FINAL_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    
    if scripts is None:
        script_file = config.WORKSPACE_DIR / "script.json"
        if not script_file.exists():
            raise FileNotFoundError(f"Chưa có file {script_file}. Vui lòng chạy Bước 2 trước.")
        with open(script_file, "r", encoding="utf-8") as f:
            scripts = json.load(f)
            
    ref_audio, ref_text = ensure_reference_sample()
    print(f"[*] Mẫu giọng tham chiếu: {Path(ref_audio).name}")
    print(f"[*] Nội dung tham chiếu: \"{ref_text}\"")
    
    cloner = get_f5_cloner()
    
    final_records = []
    for item in scripts:
        idx = item["slide_index"]
        out_wav = config.FINAL_AUDIO_DIR / f"final_slide_{idx:03d}.wav"
        out_mp3 = config.FINAL_AUDIO_DIR / f"final_slide_{idx:03d}.mp3"
        
        print(f"[*] Slide {idx}/{len(scripts)}: \"{item.get('title', '')}\"...")
        start_t = time.time()
        
        wav, sr, _ = cloner.infer(
            ref_file=ref_audio,
            ref_text=ref_text,
            gen_text=item["script"],
            file_wave=str(out_wav.resolve()),
            speed=speed,
            nfe_step=32
        )
        
        # Convert WAV to high quality MP3
        subprocess.run([
            "ffmpeg", "-y", "-i", str(out_wav.resolve()),
            "-c:a", "libmp3lame", "-b:a", "192k",
            str(out_mp3.resolve())
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if out_wav.exists():
            try: out_wav.unlink()
            except Exception: pass
            
        elapsed = round(time.time() - start_t, 1)
        dur = round(len(wav) / sr, 1) if sr > 0 else 0
        print(f"    -> [✓] Đã tạo xong bằng giọng của bạn: {out_mp3.name} ({dur}s audio trong {elapsed}s GPU)")
        
        final_records.append({
            "slide_index": idx,
            "title": item["title"],
            "script": item["script"],
            "audio_path": str(out_mp3.resolve()),
            "image_path": str((config.IMAGES_DIR / f"slide_{idx:03d}.png").resolve())
        })
        
    output_meta = config.WORKSPACE_DIR / "final_audio_meta.json"
    with open(output_meta, "w", encoding="utf-8") as f:
        json.dump(final_records, f, ensure_ascii=False, indent=2)
        
    print(f"\n[✓] Hoàn tất sinh giọng F5-TTS cho toàn bộ {len(final_records)} slide!")
    return final_records

if __name__ == "__main__":
    run_f5_voice_cloning()
