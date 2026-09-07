"""
Module: script_gen.py
Description: Sinh kịch bản sư phạm tự nhiên, truyền cảm bằng AI (Gemini / OpenAI / Offline Engine).
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Any

try:
    from . import config
except (ImportError, ValueError):
    import config

SYSTEM_PROMPT = """Bạn là một giáo sư, chuyên gia thuyết trình và giảng viên đại học xuất sắc với phong cách sư phạm đỉnh cao, truyền cảm, cuốn hút và đậm chất văn nói diễn thuyết.
Nhiệm vụ: Chuyển đổi nội dung slide bài giảng thành BÀI GIẢNG ĐIỆN TỬ DIỄN THUYẾT HOÀN CHỈNH (Lời thuyết minh lồng tiếng sống động cho video).

QUY TẮC BẮT BUỘC ĐỂ GIỌNG ĐỌC AI NHẤN NHÁ VÀ TỰ NHIÊN NHƯ NGƯỜI THẬT:
1. VĂN PHONG VĂN NÓI DIỄN THUYẾT: Tuyệt đối không đọc như đọc sách hay đọc gạch đầu dòng. Hãy dùng văn nói tự nhiên, có câu hỏi tương tác ("Vậy... câu hỏi đặt ra là gì?...", "Đúng vậy!", "Các bạn hãy chú ý điểm mấu chốt này...").
2. NGHỆ THUẬT DẤU CÂU TẠO NHỊP ĐIỆU (RẤT QUAN TRỌNG):
   - Sử dụng dấu chấm lửng `...` trước các từ khóa hoặc sau câu hỏi để tạo quãng ngắt lấy hơi kịch tính (Ví dụ: "Vậy... bản chất thực sự của vấn đề là gì?").
   - Sử dụng dấu gạch ngang `—` để nhấn mạnh ý tương phản hoặc giải thích chốt hạ.
   - Sử dụng dấu chấm than `!` tại các kết luận mang tính đúc kết hoặc truyền cảm hứng.
3. TÍCH HỢP SPEAKER NOTES: Nếu slide có Speaker Notes (ghi chú diễn giả), hãy ưu tiên khai thác sâu các tình huống thực tế, góc nhìn phân tích sâu sắc từ Speaker Notes vào bài giảng.
4. THUẬT NGỮ TIẾNG ANH: Giữ nguyên vẹn các thuật ngữ công nghệ tiếng Anh chuẩn (nhu Product Backlog, User Story, Scrum, Sprint, INVEST, DEEP, Burndown Chart, Trello, Epic, Feature, Acceptance Criteria...).
5. ĐỘ DÀI: Mỗi slide viết từ 4 - 8 câu hoàn chỉnh, giàu cảm xúc, đọc trong khoảng 35 - 55 giây.

ĐỊNH DẠNG ĐẦU RA BẮT BUỘC:
Trả về DUY NHẤT một mảng JSON (Array of Objects) hợp lệ:
[
  {
    "slide_index": 1,
    "title": "Tiêu đề của slide",
    "script": "Lời giảng diễn thuyết truyền cảm, có dấu câu ngắt nghỉ tự nhiên..."
  }
]
"""

def generate_script_gemini(slides_data: List[Dict[str, Any]], api_key: str) -> List[Dict[str, Any]]:
    """Tạo kịch bản bài giảng bằng Google Gemini API."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key.strip())
    prompt = f"Hãy đóng vai một giảng viên sư phạm xuất sắc và viết lời giảng chi tiết, truyền cảm cho từng slide dưới đây:\n\n{json.dumps(slides_data, ensure_ascii=False, indent=2)}"

    models_to_try = [config.GEMINI_MODEL, "gemini-2.5-flash", "gemini-1.5-flash"]
    last_err = None
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=SYSTEM_PROMPT),
                            types.Part.from_text(text=prompt)
                        ]
                    )
                ],
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text.strip())
        except Exception as e:
            last_err = e
            continue

    raise last_err or RuntimeError("Không thể kết nối Gemini API.")


def generate_rich_offline_script(slides_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Bộ tạo kịch bản sư phạm tự động Offline nếu không có API Key."""
    scripts = []
    total = len(slides_data)

    for s in slides_data:
        idx = s["slide_index"]
        title = s.get("title", f"Nội dung số {idx}").strip()
        bullets = s.get("bullet_points", [])
        notes = s.get("speaker_notes", "").strip()

        paragraphs = []
        if idx == 1:
            paragraphs.append(f"Chào mừng tất cả các bạn học viên đã đến với bài học hôm nay. Trong bài giảng này, chúng ta sẽ cùng nhau tìm hiểu một chủ đề vô cùng quan trọng: {title}.")
        elif idx == total:
            paragraphs.append(f"Để khép lại bài học hôm nay, chúng ta cùng đi đến phần tổng kết và đúc kết về: {title}.")
        else:
            paragraphs.append(f"Tiếp nối nội dung vừa rồi, bây giờ chúng ta sẽ cùng nhau chuyển sang phần trọng tâm tiếp theo, đó là: {title}.")

        if notes:
            cleaned_notes = notes.replace("•", "").strip()
            paragraphs.append(f"Như chúng ta đã biết, {cleaned_notes}")

        if bullets:
            connectors = [
                "Trước hết, điểm cốt lõi đầu tiên mà các bạn cần lưu ý chính là",
                "Bên cạnh đó, một yếu tố đặc biệt quan trọng tiếp theo là",
                "Hơn thế nữa, trong thực tế triển khai, chúng ta thấy rằng",
                "Đồng thời, để đạt được hiệu quả tối ưu, các bạn cần chú ý đến",
                "Và cuối cùng, một khía cạnh không thể bỏ qua chính là"
            ]
            for i, b in enumerate(bullets):
                cleaned = b.lstrip("0123456789.-•* ").strip()
                if not cleaned:
                    continue
                conn = connectors[i % len(connectors)]
                if cleaned.endswith("."):
                    cleaned = cleaned[:-1]

                if len(cleaned.split()) < 6:
                    paragraphs.append(f"{conn} vấn đề {cleaned}. Điều này đóng vai trò then chốt trong bài học.")
                else:
                    first_char = cleaned[0].lower() if len(cleaned) > 1 else cleaned
                    rest = cleaned[1:] if len(cleaned) > 1 else ""
                    paragraphs.append(f"{conn} {first_char}{rest}.")

        if idx == total:
            paragraphs.append("Hi vọng rằng qua bài học này, các bạn đã nắm vững toàn bộ kiến thức và có thể tự tin ứng dụng vào thực tế. Cảm ơn các bạn đã chú ý theo dõi!")
        else:
            paragraphs.append("Các bạn hãy ghi nhớ những điểm trọng tâm này trước khi chúng ta tiếp tục sang slide tiếp theo.")

        scripts.append({
            "slide_index": idx,
            "title": title,
            "script": " ".join(paragraphs)
        })

    return scripts


def run_script_generator(input_data: List[Dict[str, Any]] = None, gemini_api_key: str = None) -> List[Dict[str, Any]]:
    """Hàm thực thi chính cho Bước 2: Tạo Kịch Bản Sư Phạm"""
    if input_data is None:
        extracted_file = config.WORKSPACE_DIR / "extracted_data.json"
        if not extracted_file.exists():
            raise FileNotFoundError(f"Chưa có file {extracted_file}. Vui lòng chạy Bước 1 trước.")
        with open(extracted_file, "r", encoding="utf-8") as f:
            input_data = json.load(f)

    api_key = gemini_api_key or config.GEMINI_API_KEY
    scripts = None

    if api_key:
        try:
            scripts = generate_script_gemini(input_data, api_key)
        except Exception as e:
            print(f"[!] Gemini API Error: {e}. Fallback to Offline script engine.")

    if scripts is None:
        scripts = generate_rich_offline_script(input_data)

    output_script_file = config.WORKSPACE_DIR / "script.json"
    with open(output_script_file, "w", encoding="utf-8") as f:
        json.dump(scripts, f, ensure_ascii=False, indent=2)

    return scripts

run_step2 = run_script_generator
