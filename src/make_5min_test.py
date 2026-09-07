import os
import sys
import json
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path("src").resolve()))
import config
from step4_rvc import run_step4
from step5_video import run_step5

# Load base audio meta
with open("workspace/base_audio_meta.json", "r", encoding="utf-8") as f:
    all_records = json.load(f)

# Select first 10 slides (~5 minutes 16 seconds)
selected_records = all_records[:10]
print(f"[*] Chon {len(selected_records)} slide dau tien de tao video test 5 phut...")

# Run Step 4 (RVC conversion with 100-Epoch model, index_rate=0.92, protect=0.15)
final_records = run_step4(audio_records=selected_records, enable_rvc=True)

# Run Step 5 (Video assembly)
out_video = run_step5(slide_items=final_records, output_name="output_video_5min.mp4")
print(f"\n[DONE] Video test 5 phut da tao thanh cong: {out_video}")
