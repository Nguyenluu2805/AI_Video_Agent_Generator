import asyncio
import re
import subprocess
from pathlib import Path
import edge_tts

out_dir = Path("voice_samples/test_seamless_bilingual")
out_dir.mkdir(parents=True, exist_ok=True)

ENGLISH_TERMS = [
    r"Product Backlog", r"User Story", r"Scrum", r"Sprint", r"INVEST", r"DEEP",
    r"Burndown Chart", r"Trello", r"Epic", r"Feature", r"Acceptance Criteria",
    r"Definition of Done", r"Single Source of Truth", r"GoRide", r"Scrum Guide",
    r"Given-When-Then", r"Given", r"When", r"Then"
]

def split_bilingual_text(text: str):
    pattern = r"(" + "|".join([re.escape(t) for t in ENGLISH_TERMS]) + r")"
    raw_tokens = re.split(pattern, text, flags=re.IGNORECASE)
    segments = []
    for tok in raw_tokens:
        if not tok or not tok.strip():
            continue
        is_en = any(re.fullmatch(re.escape(t), tok.strip(), re.IGNORECASE) for t in ENGLISH_TERMS)
        clean_tok = tok.strip()
        if clean_tok:
            segments.append((clean_tok, "en" if is_en else "vi"))
    return segments

async def render_seamless_bilingual(text: str, output_mp3: Path):
    segments = split_bilingual_text(text)
    temp_files = []
    
    for i, (seg_text, lang) in enumerate(segments):
        voice = "en-US-AndrewMultilingualNeural" if lang == "en" else "vi-VN-NamMinhNeural"
        rate = "-2%" if lang == "en" else "-4%"
        seg_file = out_dir / f"seg_{i:03d}.mp3"
        comm = edge_tts.Communicate(text=seg_text, voice=voice, rate=rate)
        await comm.save(str(seg_file.resolve()))
        temp_files.append(seg_file)
        
    concat_list = out_dir / "concat_list.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for fpath in temp_files:
            p = str(fpath.resolve()).replace("\\", "/")
            f.write(f"file '{p}'\n")
            
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_list.resolve()),
        "-c:a", "libmp3lame", "-b:a", "192k",
        str(output_mp3.resolve())
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    print(f"[✓] Generated seamless bilingual audio: {output_mp3.name} ({round(output_mp3.stat().st_size/1024, 1)} KB)")

async def main():
    test_slide_1 = "Chào mừng tất cả các bạn học viên đã quay trở lại với bài học Product Backlog và User Story trong mô hình Scrum! Hôm nay... chúng ta sẽ cùng nhau làm chủ các kỹ thuật phân rã yêu cầu, bộ tiêu chí INVEST và cách kiểm soát tiến độ bằng Burndown Chart trên Trello."
    out_file = out_dir / "seamless_bilingual_slide1.mp3"
    await render_seamless_bilingual(test_slide_1, out_file)

asyncio.run(main())
