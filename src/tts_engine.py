"""
Module: tts_engine.py
Description: Động cơ tổng hợp giọng đọc Text-To-Speech (Microsoft Edge Neural TTS & EverAI Multilingual API).
"""

import os
import sys
import json
import re
import asyncio
import time
import requests
from pathlib import Path
from typing import List, Dict, Any

try:
    from . import config
except (ImportError, ValueError):
    import config

EVERAI_BASE_URL = "https://www.everai.vn/api/v1/tts"

def clean_text_for_tts(text: str) -> str:
    """Chuẩn hóa văn bản, mở rộng ký hiệu và thuật ngữ tiếng Anh."""
    text = text.replace("%", " phần trăm")
    text = text.replace("&", " và ")
    text = text.replace(" - ", ", ")
    text = text.replace(":", ", ")

    text = re.sub(r'\b([A-Za-z])\.([A-Za-z])\.([A-Za-z])\.([A-Za-z])\b', r'\1\2\3\4', text)
    text = re.sub(r'\b([A-Za-z])\.([A-Za-z])\.([A-Za-z])\b', r'\1\2\3', text)
    text = re.sub(r'\b([A-Za-z])\.([A-Za-z])\b', r'\1\2', text)

    text = re.sub(r'[\*\#\_\[\]\(\)\{\}\<\>]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


async def synthesize_edge_tts(text: str, voice: str, output_path: Path, max_retries: int = 5) -> bool:
    """Tổng hợp giọng bằng Microsoft Neural TTS (Edge TTS)."""
    import edge_tts

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
    raise last_err or RuntimeError(f"Không thể sinh âm thanh EdgeTTS sau {max_retries} lần thử.")


def synthesize_everai(
    text: str,
    output_path: Path,
    voice_code: str = "vi_male_lehoang_mb",
    api_key: str = None,
    timeout_secs: int = 120
) -> Path:
    """Tổng hợp giọng bằng EverAI Multilingual API."""
    key = api_key or config.EVERAI_API_KEY
    if not key:
        raise ValueError("Chưa cấu hình EVERAI_API_KEY trong .env hoặc giao diện.")

    headers = {
        "Authorization": f"Bearer {key.strip()}",
        "Content-Type": "application/json"
    }

    payload = {
        "input_text": clean_text_for_tts(text),
        "voice_code": voice_code,
        "model_id": "everai-v1.6",
        "audio_type": "mp3",
        "bitrate": 128,
        "speed_rate": 1.0,
        "pitch_rate": 1.0
    }

    resp = requests.post(EVERAI_BASE_URL, json=payload, headers=headers, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"EverAI API Error ({resp.status_code}): {resp.text}")

    data = resp.json()
    if data.get("status") != 1 or "result" not in data:
        err_msg = data.get("error_message", "Unknown error")
        raise RuntimeError(f"EverAI Error: {err_msg}")

    request_id = data["result"]["request_id"]
    get_url = f"{EVERAI_BASE_URL}/{request_id}"

    start_time = time.time()
    while time.time() - start_time < timeout_secs:
        status_resp = requests.get(get_url, headers=headers, timeout=15)
        if status_resp.status_code == 200:
            status_data = status_resp.json()
            res = status_data.get("result", {})
            status = res.get("status", "").lower()

            if status in ["done", "success"]:
                audio_link = res.get("audio_link")
                if not audio_link:
                    raise RuntimeError(f"EverAI task {request_id} không có audio_link.")
                audio_bytes = requests.get(audio_link, timeout=60).content
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(audio_bytes)
                return output_path
            elif status in ["fail", "failed", "error"]:
                raise RuntimeError(f"EverAI xử lý thất bại cho request: {request_id}")

        time.sleep(1.5)

    raise TimeoutError(f"EverAI timeout ({timeout_secs}s) cho request: {request_id}")


async def synthesize_all_audio_async(scripts: List[Dict[str, Any]], voice_name: str = None) -> List[Dict[str, Any]]:
    """Tổng hợp toàn bộ âm thanh mới cho các slide theo đúng kịch bản hiện tại."""
    config.BASE_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    
    # Xóa sạch các file âm thanh cũ trong workspace để không dùng lại bài cũ
    for old_file in config.BASE_AUDIO_DIR.glob("slide_*.mp3"):
        try: old_file.unlink()
        except Exception: pass

    audio_records = []
    selected_voice = voice_name or config.TTS_VOICE or "vi-VN-NamMinhNeural"
    is_everai = selected_voice.startswith("voice-") or selected_voice.startswith("vi_")

    for item in scripts:
        idx = item["slide_index"]
        audio_file = config.BASE_AUDIO_DIR / f"slide_{idx:03d}.mp3"

        if is_everai:
            synthesize_everai(item["script"], audio_file, voice_code=selected_voice)
        else:
            await synthesize_edge_tts(item["script"], selected_voice, audio_file)
        await asyncio.sleep(0.3)

        audio_records.append({
            "slide_index": idx,
            "title": item.get("title", f"Slide {idx}"),
            "script": item["script"],
            "base_audio_path": str(audio_file.resolve())
        })

    return audio_records


def run_tts_engine(scripts: List[Dict[str, Any]] = None, voice_name: str = None) -> List[Dict[str, Any]]:
    """Hàm thực thi chính cho Bước 3: Tổng hợp Audio TTS"""
    if scripts is None:
        script_file = config.WORKSPACE_DIR / "script.json"
        if not script_file.exists():
            raise FileNotFoundError(f"Chưa có file {script_file}. Vui lòng chạy Bước 2 trước.")
        with open(script_file, "r", encoding="utf-8") as f:
            scripts = json.load(f)

    audio_records = asyncio.run(synthesize_all_audio_async(scripts, voice_name=voice_name))

    output_meta = config.WORKSPACE_DIR / "base_audio_meta.json"
    with open(output_meta, "w", encoding="utf-8") as f:
        json.dump(audio_records, f, ensure_ascii=False, indent=2)

    return audio_records

run_step3 = run_tts_engine
