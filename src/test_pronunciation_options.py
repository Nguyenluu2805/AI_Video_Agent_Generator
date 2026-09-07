import asyncio
import edge_tts
from pathlib import Path

test_text_raw = "Chào mừng các bạn học viên đã quay trở lại với bài học Product Backlog và User Story trong mô hình Scrum. Chúng ta sẽ cùng tìm hiểu về tiêu chí INVEST và biểu đồ Burndown Chart trên Trello."
test_text_phonetic = "Chào mừng các bạn học viên đã quay trở lại với bài học Prót-đắc Bách-lóc và Diu-sơ Xto-ri trong mô hình X-cram. Chúng ta sẽ cùng tìm hiểu về tiêu chí In-vét và biểu đồ Bơn-đao Chạt trên Trét-lô."

out_dir = Path("voice_samples/test_pronunciation")
out_dir.mkdir(parents=True, exist_ok=True)

async def generate(text, voice, out_name):
    out_path = out_dir / out_name
    comm = edge_tts.Communicate(text, voice)
    await comm.save(str(out_path.resolve()))
    print(f"[✓] Generated {out_name} with voice {voice} ({round(out_path.stat().st_size/1024, 1)} KB)")

async def main():
    # Option 1: Microsoft Nam Minh with natural English words (NO phonetic butchering)
    await generate(test_text_raw, "vi-VN-NamMinhNeural", "1_namminh_natural.mp3")
    
    # Option 2: Microsoft Nam Minh with current phonetic dictionary ("Prót-đắc Bách-lóc")
    await generate(test_text_phonetic, "vi-VN-NamMinhNeural", "2_namminh_phonetic.mp3")
    
    # Option 3: Microsoft Andrew Multilingual (Native English + Multilingual)
    await generate(test_text_raw, "en-US-AndrewMultilingualNeural", "3_andrew_multilingual.mp3")
    
    # Option 4: Microsoft Brian Multilingual
    await generate(test_text_raw, "en-US-BrianMultilingualNeural", "4_brian_multilingual.mp3")

asyncio.run(main())
