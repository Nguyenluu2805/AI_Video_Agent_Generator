import asyncio
import edge_tts
from pathlib import Path

out_dir = Path("voice_samples/test_expressive")
out_dir.mkdir(parents=True, exist_ok=True)

# 1. Ban doc thong thuong (Doc deu deu, van viet)
text_flat = "Product Backlog là danh sách các yêu cầu được sắp xếp theo thứ tự ưu tiên. Nếu không có Backlog rõ ràng thì dự án sẽ gặp nhiều rủi ro và trễ hạn."

# 2. Ban doc dien cam (Van noi giang day, co cau hoi tu tu, ngat nghi, nhan manh bang dau cau)
text_expressive = "Vậy... Product Backlog thực chất là gì? Đó chính là danh sách các yêu cầu — được sắp xếp theo thứ tự ưu tiên sống còn của sản phẩm! Hãy nhớ rằng: nếu không có một Backlog rõ ràng... dự án của bạn chắc chắn sẽ rơi vào hỗn loạn và trễ hạn!"

async def generate(text, rate, out_name):
    out_path = out_dir / out_name
    comm = edge_tts.Communicate(text=text, voice="vi-VN-NamMinhNeural", rate=rate)
    await comm.save(str(out_path.resolve()))
    print(f"[✓] Generated {out_name} ({round(out_path.stat().st_size/1024, 1)} KB)")

async def main():
    # Mau A: Ban cu (Deu deu)
    await generate(text_flat, "+0%", "A_flat_voice.mp3")
    
    # Mau B: Ban nhan nha dien cam (+0% toc do)
    await generate(text_expressive, "+0%", "B_expressive_normal_speed.mp3")
    
    # Mau C: Ban nhan nha + giang cham rai truyen cam (-4% toc do)
    await generate(text_expressive, "-4%", "C_expressive_pedagogy_speed.mp3")

asyncio.run(main())
