import os
import sys
import io
from pathlib import Path
from dotenv import load_dotenv

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Base paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_ROOT / "input"
MODELS_DIR = PROJECT_ROOT / "models"
WORKSPACE_DIR = PROJECT_ROOT / "workspace"
IMAGES_DIR = WORKSPACE_DIR / "images"
BASE_AUDIO_DIR = WORKSPACE_DIR / "base_audio"
FINAL_AUDIO_DIR = WORKSPACE_DIR / "final_audio"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Load environment variables
load_dotenv(PROJECT_ROOT / ".env")

# Ensure required directories exist
for p in [INPUT_DIR, MODELS_DIR, WORKSPACE_DIR, IMAGES_DIR, BASE_AUDIO_DIR, FINAL_AUDIO_DIR, OUTPUT_DIR]:
    p.mkdir(parents=True, exist_ok=True)

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
EVERAI_API_KEY = os.getenv("EVERAI_API_KEY", "")

# TTS Configuration
# TTS_ENGINE: "edge-tts" (Microsoft Neural) or "gtts" (Google TTS fast)
TTS_ENGINE = os.getenv("TTS_ENGINE", "edge-tts").lower()
TTS_VOICE = os.getenv("TTS_VOICE", "vi-VN-NamMinhNeural")
TTS_RATE = os.getenv("TTS_RATE", "-4%")
TTS_VOLUME = os.getenv("TTS_VOLUME", "+0%")

# RVC (Voice Cloning) Configuration
RVC_MODEL_PATH = os.getenv("RVC_MODEL_PATH", str(MODELS_DIR / "my_voice.pth"))
RVC_INDEX_PATH = os.getenv("RVC_INDEX_PATH", str(MODELS_DIR / "my_voice.index"))
RVC_PITCH = int(os.getenv("RVC_PITCH", "0"))
RVC_F0_METHOD = os.getenv("RVC_F0_METHOD", "rmvpe")
RVC_INDEX_RATE = float(os.getenv("RVC_INDEX_RATE", "0.75"))
RVC_DEVICE = os.getenv("RVC_DEVICE", "cuda:0")

# Video Rendering Configuration
VIDEO_WIDTH = int(os.getenv("VIDEO_WIDTH", "1920"))
VIDEO_HEIGHT = int(os.getenv("VIDEO_HEIGHT", "1080"))
VIDEO_FPS = int(os.getenv("VIDEO_FPS", "24"))
SLIDE_PAUSE_DURATION = float(os.getenv("SLIDE_PAUSE_DURATION", "0.6"))
