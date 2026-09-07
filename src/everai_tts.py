import os
import sys
import time
import requests
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import config

EVERAI_BASE_URL = "https://www.everai.vn/api/v1/tts"

def synthesize_everai(
    text: str,
    output_path: Path,
    api_key: str = None,
    voice_code: str = "vi_male_lehoang_mb",
    model_id: str = "everai-v1.6",
    speed_rate: float = 1.0,
    pitch_rate: float = 1.0,
    timeout_secs: int = 120
) -> Path:
    """
    Synthesize audio using EverAI Text-to-Speech API (everai-v1.6 multilingual model).
    """
    api_key = api_key or os.getenv("EVERAI_API_KEY")
    if not api_key:
        raise ValueError(
            "Chưa cấu hình EVERAI_API_KEY! Vui lòng đăng ký tài khoản tại https://everai.vn "
            "và điền API Key vào file .env (EVERAI_API_KEY=your_key_here)."
        )

    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json"
    }

    payload = {
        "input_text": text,
        "voice_code": voice_code,
        "model_id": model_id,
        "audio_type": "mp3",
        "bitrate": 128,
        "speed_rate": speed_rate,
        "pitch_rate": pitch_rate
    }

    # 1. Send synthesis POST request
    resp = requests.post(EVERAI_BASE_URL, json=payload, headers=headers, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"EverAI API Error ({resp.status_code}): {resp.text}")

    data = resp.json()
    if data.get("status") != 1 or "result" not in data:
        err_msg = data.get("error_message", "Unknown error")
        raise RuntimeError(f"EverAI Error: {err_msg}")

    request_id = data["result"]["request_id"]
    get_url = f"{EVERAI_BASE_URL}/{request_id}"

    # 2. Poll for completion
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
                    raise RuntimeError(f"EverAI task {request_id} hoàn tất nhưng không có audio_link.")
                
                # 3. Download audio file
                audio_bytes = requests.get(audio_link, timeout=60).content
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(audio_bytes)
                return output_path
                
            elif status in ["fail", "failed", "failure", "error"]:
                raise RuntimeError(f"EverAI xử lý thất bại cho request_id: {request_id}")
                
        time.sleep(1.5)

    raise TimeoutError(f"EverAI xử lý quá thời gian chờ ({timeout_secs}s) cho request_id: {request_id}")
