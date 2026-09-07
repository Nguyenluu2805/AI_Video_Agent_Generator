import asyncio
import re
import edge_tts
import subprocess
from pathlib import Path

out_dir = Path("voice_samples/test_pronunciation")

async def generate_segment(text, voice, out_file):
    comm = edge_tts.Communicate(text, voice)
    await comm.save(str(out_file.resolve()))

async def main():
    # Segment 1: VI
    await generate_segment("Chào mừng các bạn học viên đã quay trở lại với bài học ", "vi-VN-NamMinhNeural", out_dir / "s1.mp3")
    # Segment 2: EN
    await generate_segment("Product Backlog", "en-US-AndrewMultilingualNeural", out_dir / "s2.mp3")
    # Segment 3: VI
    await generate_segment(" và ", "vi-VN-NamMinhNeural", out_dir / "s3.mp3")
    # Segment 4: EN
    await generate_segment("User Story", "en-US-AndrewMultilingualNeural", out_dir / "s4.mp3")
    # Segment 5: VI
    await generate_segment(" trong mô hình ", "vi-VN-NamMinhNeural", out_dir / "s5.mp3")
    # Segment 6: EN
    await generate_segment("Scrum", "en-US-AndrewMultilingualNeural", out_dir / "s6.mp3")
    # Segment 7: VI
    await generate_segment(". Chúng ta sẽ cùng tìm hiểu về tiêu chí ", "vi-VN-NamMinhNeural", out_dir / "s7.mp3")
    # Segment 8: EN
    await generate_segment("INVEST", "en-US-AndrewMultilingualNeural", out_dir / "s8.mp3")
    # Segment 9: VI
    await generate_segment(" và biểu đồ ", "vi-VN-NamMinhNeural", out_dir / "s9.mp3")
    # Segment 10: EN
    await generate_segment("Burndown Chart", "en-US-AndrewMultilingualNeural", out_dir / "s10.mp3")
    # Segment 11: VI
    await generate_segment(" trên ", "vi-VN-NamMinhNeural", out_dir / "s11.mp3")
    # Segment 12: EN
    await generate_segment("Trello.", "en-US-AndrewMultilingualNeural", out_dir / "s12.mp3")

    # Concat with ffmpeg
    concat_txt = out_dir / "concat.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for i in range(1, 13):
            p = str((out_dir / f"s{i}.mp3").resolve()).replace("\\", "/")
            f.write(f"file '{p}'\n")

    out_final = out_dir / "5_bilingual_spliced.mp3"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_txt.resolve()),
        "-c:a", "libmp3lame", "-b:a", "192k",
        str(out_final.resolve())
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"[✓] Generated 5_bilingual_spliced.mp3 successfully ({round(out_final.stat().st_size/1024, 1)} KB)")

asyncio.run(main())
