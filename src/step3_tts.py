import os
import sys
import json
import re
import asyncio
import time
from pathlib import Path
import edge_tts

# Add parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import config
from phonetics import normalize_phonetics

def clean_text_for_tts(text: str) -> str:
    """Clean markdown artifacts, dots in acronyms, percentages, and normalize English phonetics."""
    # 1. Expand percentages and common symbols
    text = text.replace("%", " phần trăm")
    text = text.replace("&", " và ")
    text = text.replace(" - ", ", ")
    text = text.replace(":", ", ")
    
    # 2. Fix dotted acronyms like D.E.E.P -> DEEP, I.N.V.E.S.T -> INVEST
    text = re.sub(r'\b([A-Za-z])\.([A-Za-z])\.([A-Za-z])\.([A-Za-z])\b', r'\1\2\3\4', text)
    text = re.sub(r'\b([A-Za-z])\.([A-Za-z])\.([A-Za-z])\b', r'\1\2\3', text)
    text = re.sub(r'\b([A-Za-z])\.([A-Za-z])\b', r'\1\2', text)
    
    # 3. Clean markdown formatting
    text = re.sub(r'[\*\#\_\[\]\(\)\{\}\<\>]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

async def generate_single_audio_with_retry(text: str, voice: str, output_path: Path, max_retries: int = 5):
    """Generate authentic neural voice with automatic retry and timeout mechanism."""
    cleaned = clean_text_for_tts(text)
    rate = config.TTS_RATE or "+0%"
    volume = config.TTS_VOLUME or "+0%"
    
    last_err = None
    for attempt in range(1, max_retries + 1):
        if output_path.exists() and output_path.stat().st_size == 0:
            try: output_path.unlink()
            except Exception: pass
            
        try:
            communicate = edge_tts.Communicate(text=cleaned, voice=voice, rate=rate, volume=volume)
            await asyncio.wait_for(communicate.save(str(output_path.resolve())), timeout=45.0)
            if output_path.exists() and output_path.stat().st_size > 1024:
                return True
        except Exception as e:
            last_err = e
            if attempt < max_retries:
                await asyncio.sleep(2.0 * attempt)
                
    if output_path.exists() and output_path.stat().st_size == 0:
        try: output_path.unlink()
        except Exception: pass
    raise last_err or RuntimeError(f"Không thể sinh âm thanh sau {max_retries} lần thử")

def generate_single_audio_everai(text: str, voice_code: str, output_path: Path):
    """Generate audio using EverAI API."""
    from everai_tts import synthesize_everai
    cleaned = clean_text_for_tts(text)
    synthesize_everai(
        text=cleaned,
        output_path=output_path,
        voice_code=voice_code or "voice-9c25f795-6ed9-4fd4",
        model_id="everai-v1.6"
    )
    return True

async def generate_all_audio_async(scripts: list, voice_name: str = None) -> list:
    """Generate audio files for all slides with genuine Microsoft Neural voices."""
    config.BASE_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    audio_records = []
    
    selected_voice = voice_name or config.TTS_VOICE or "vi-VN-NamMinhNeural"
    
    # Map friendly names
    if selected_voice.lower() in ["male", "nam", "giọng nam", "vi-vn-namminhneural"]:
        selected_voice = "vi-VN-NamMinhNeural"
    elif selected_voice.lower() in ["female", "nu", "nữ", "giọng nữ", "vi-vn-hoaimyneural"]:
        selected_voice = "vi-VN-HoaiMyNeural"
        
    is_male = "nam" in selected_voice.lower()
    voice_label = "GIỌNG NAM (Microsoft Nam Minh Neural)" if is_male else "GIỌNG NỮ (Microsoft Hoài My Neural)"
    print(f"[*] Chế độ: {voice_label} | Đang sinh âm thanh cho {len(scripts)} slides...")
    
    for item in scripts:
        idx = item["slide_index"]
        audio_file = config.BASE_AUDIO_DIR / f"slide_{idx:03d}.mp3"
        
        # Check if already generated valid audio
        if audio_file.exists() and audio_file.stat().st_size > 2048:
            size_kb = round(audio_file.stat().st_size / 1024, 1)
            print(f"[*] Slide {idx}/{len(scripts)}: \"{item.get('title', '')}\" -> [Đã có sẵn: {size_kb} KB]")
        else:
            print(f"[*] Slide {idx}/{len(scripts)}: \"{item.get('title', '')}\"...")
            if config.TTS_ENGINE == "everai" or selected_voice.startswith("voice-") or selected_voice.startswith("vi_"):
                generate_single_audio_everai(item["script"], selected_voice, audio_file)
            else:
                await generate_single_audio_with_retry(item["script"], selected_voice, audio_file)
            size_kb = round(audio_file.stat().st_size / 1024, 1)
            print(f"    -> [✓] Đã tạo xong: {audio_file.name} ({size_kb} KB)")
            await asyncio.sleep(0.5)
        
        audio_records.append({
            "slide_index": idx,
            "title": item.get("title", f"Slide {idx}"),
            "script": item["script"],
            "base_audio_path": str(audio_file.resolve())
        })
        
    return audio_records

def run_step3(scripts: list = None, voice_name: str = None) -> list:
    """
    Main function for Step 3: Base TTS
    """
    print(f"\n=======================================================")
    print(f"[Bước 3/5] Sinh Giọng Đọc Lồng Tiếng (Microsoft Neural TTS)")
    print(f"=======================================================")
    
    if scripts is None:
        script_file = config.WORKSPACE_DIR / "script.json"
        if not script_file.exists():
            raise FileNotFoundError(f"Chưa có file {script_file}. Vui lòng chạy Bước 2 trước.")
        with open(script_file, "r", encoding="utf-8") as f:
            scripts = json.load(f)
            
    audio_records = asyncio.run(generate_all_audio_async(scripts, voice_name=voice_name))
    
    output_meta = config.WORKSPACE_DIR / "base_audio_meta.json"
    with open(output_meta, "w", encoding="utf-8") as f:
        json.dump(audio_records, f, ensure_ascii=False, indent=2)
        
    print(f"[✓] Hoàn thành Bước 3. Đã tạo {len(audio_records)} file âm thanh chuẩn tại: {config.BASE_AUDIO_DIR}")
    return audio_records

if __name__ == "__main__":
    run_step3(voice_name="vi-VN-NamMinhNeural")
