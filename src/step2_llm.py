import os
import sys
import json
import re
from pathlib import Path

# Add parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import config

SYSTEM_PROMPT = """Bạn là một giáo sư, chuyên gia thuyết trình và giảng viên đại học xuất sắc với phong cách sư phạm đỉnh cao, truyền cảm, cuốn hút và đậm chất văn nói diễn thuyết.
Nhiệm vụ: Chuyển đổi nội dung slide bài giảng thành BÀI GIẢNG ĐIỆN TỬ DIỄN THUYẾT HOÀN CHỈNH (Lời thuyết minh lồng tiếng sống động cho video).

QUY TẮC BẮT BUỘC ĐỂ GIỌNG ĐỌC AI NHẤN NHÁ VÀ TỰ NHIÊN NHƯ NGƯỜI THẬT:
1. VĂN PHONG VĂN NÓI DIỄN THUYẾT: Tuyệt đối không đọc như đọc sách hay đọc gạch đầu dòng. Hãy dùng văn nói tự nhiên, có câu hỏi tương tác ("Vậy... câu hỏi đặt ra là gì?...", "Đúng vậy!", "Các bạn hãy chú ý điểm mấu chốt này...").
2. NGHỆ THUẬT DẤU CÂU TẠO NHỊP ĐIỆU (RẤT QUAN TRỌNG):
   - Sử dụng dấu chấm lửng `...` trước các từ khóa hoặc sau câu hỏi để tạo quãng ngắt lấy hơi kịch tính (Ví dụ: "Vậy... bản chất thực sự của vấn đề là gì?").
   - Sử dụng dấu gạch ngang `—` để nhấn mạnh ý tương phản hoặc giải thích chốt hạ (Ví dụ: "Đó không chỉ là một danh sách việc cần làm — mà là huyết mạch của toàn bộ dự án!").
   - Sử dụng dấu chấm than `!` tại các kết luận mang tính đúc kết hoặc truyền cảm hứng.
3. TÍCH HỢP SPEAKER NOTES: Nếu slide có Speaker Notes (ghi chú diễn giả), hãy ưu tiên khai thác sâu các tình huống thực tế, góc nhìn phân tích sâu sắc từ Speaker Notes vào bài giảng.
4. THUẬT NGỮ TIẾNG ANH: Giữ nguyên vẹn các thuật ngữ công nghệ tiếng Anh chuẩn (như Product Backlog, User Story, Scrum, Sprint, INVEST, DEEP, Burndown Chart, Trello, Epic, Feature, Acceptance Criteria...).
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

def generate_script_gemini(slides_data: list, api_key: str) -> list:
    """Generate teaching script using Google Gemini API."""
    from google import genai
    from google.genai import types
    
    client = genai.Client(api_key=api_key)
    prompt = f"Hãy đóng vai một giảng viên sư phạm xuất sắc và viết lời giảng chi tiết, truyền cảm cho từng slide dưới đây:\n\n{json.dumps(slides_data, ensure_ascii=False, indent=2)}"
    
    # Try gemini-2.5-flash or gemini-1.5-flash
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
            text = response.text.strip()
            return json.loads(text)
        except Exception as e:
            last_err = e
            continue
            
    raise last_err

def generate_script_openai(slides_data: list, api_key: str) -> list:
    """Generate teaching script using OpenAI API."""
    from openai import OpenAI
    
    client = OpenAI(api_key=api_key, base_url=config.OPENAI_BASE_URL)
    prompt = f"Hãy viết kịch bản lời giảng sư phạm chi tiết cho từng slide:\n\n{json.dumps(slides_data, ensure_ascii=False, indent=2)}"
    
    response = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        response_format={"type": "json_object"}
    )
    
    content = response.choices[0].message.content
    parsed = json.loads(content)
    if isinstance(parsed, dict) and "slides" in parsed:
        return parsed["slides"]
    elif isinstance(parsed, list):
        return parsed
    elif isinstance(parsed, dict) and len(parsed.keys()) == 1:
        return list(parsed.values())[0]
    return parsed

def generate_rich_offline_script(slides_data: list) -> list:
    """
    Advanced pedagogical offline script synthesizer.
    Generates rich, flowing, human-like teaching lectures instead of raw bullet points.
    """
    print("[*] Đang sử dụng bộ tạo kịch bản sư phạm chuyên sâu Offline (Phân tích ngữ cảnh & diễn giải đa tầng)...")
    
    scripts = []
    total = len(slides_data)
    
    for s in slides_data:
        idx = s["slide_index"]
        title = s.get("title", f"Nội dung số {idx}").strip()
        bullets = s.get("bullet_points", [])
        notes = s.get("speaker_notes", "").strip()
        
        paragraphs = []
        
        # 1. Slide Intro / Transition
        if idx == 1:
            paragraphs.append(f"Chào mừng tất cả các bạn học viên và quý vị theo dõi đã đến với bài học hôm nay. Trong bài giảng này, chúng ta sẽ cùng nhau tìm hiểu một chủ đề vô cùng quan trọng và thực tiễn, đó chính là: {title}.")
        elif idx == total:
            paragraphs.append(f"Để khép lại bài học ngày hôm nay, chúng ta cùng đi đến phần tổng kết và đánh giá về: {title}.")
        else:
            paragraphs.append(f"Tiếp nối nội dung vừa rồi, bây giờ chúng ta sẽ cùng nhau chuyển sang phần trọng tâm tiếp theo của bài giảng, đó là: {title}.")
            
        # 2. Integrate Speaker Notes if available
        if notes:
            cleaned_notes = notes.replace("•", "").strip()
            paragraphs.append(f"Như chúng ta đã biết, {cleaned_notes}")
            
        # 3. Rich Bullet Point Elaboration (Turning dry bullets into fluent teaching sentences)
        if bullets:
            connectors = [
                "Trước hết, điểm cốt lõi đầu tiên mà các bạn cần lưu ý chính là",
                "Bên cạnh đó, một yếu tố đặc biệt quan trọng tiếp theo là",
                "Hơn thế nữa, trong thực tế áp dụng, chúng ta thấy rằng",
                "Đồng thời, để đảm bảo hiệu quả tối ưu, các bạn cần chú ý đến",
                "Và cuối cùng, một khía cạnh không thể bỏ qua chính là"
            ]
            
            for i, b in enumerate(bullets):
                cleaned = b.lstrip("0123456789.-•* ").strip()
                if not cleaned:
                    continue
                conn = connectors[i % len(connectors)]
                
                # Make into a natural pedagogical sentence
                if cleaned.endswith("."):
                    cleaned = cleaned[:-1]
                    
                # If bullet is short, expand context
                if len(cleaned.split()) < 6:
                    paragraphs.append(f"{conn} vấn đề {cleaned}. Điều này đóng vai trò then chốt giúp bài giảng đạt được hiệu quả cao nhất.")
                else:
                    # Lowercase first letter if connector precedes it
                    first_char = cleaned[0].lower() if len(cleaned) > 1 else cleaned
                    rest = cleaned[1:] if len(cleaned) > 1 else ""
                    paragraphs.append(f"{conn} {first_char}{rest}.")
                    
        # 4. Slide Conclusion
        if idx == total:
            paragraphs.append("Hi vọng rằng qua bài học này, các bạn đã nắm vững toàn bộ kiến thức và có thể tự tin ứng dụng vào thực tế. Cảm ơn các bạn đã chú ý lắng nghe và chúc các bạn học tập thật tốt!")
        else:
            paragraphs.append("Các bạn hãy dành ít giây để ghi nhớ những điểm trọng tâm này, trước khi chúng ta cùng khám phá trang slide tiếp theo.")
            
        full_script = " ".join(paragraphs)
        scripts.append({
            "slide_index": idx,
            "title": title,
            "script": full_script
        })
        
    return scripts

def run_step2(input_data: list = None) -> list:
    """
    Main function for Step 2: LLM Script Writer
    """
    print(f"\n=======================================================")
    print(f"[Bước 2/5] Tạo Kịch Bản Giảng Dạy Bằng AI")
    print(f"=======================================================")
    
    if input_data is None:
        extracted_file = config.WORKSPACE_DIR / "extracted_data.json"
        if not extracted_file.exists():
            raise FileNotFoundError(f"Chưa có file {extracted_file}. Vui lòng chạy Bước 1 trước.")
        with open(extracted_file, "r", encoding="utf-8") as f:
            input_data = json.load(f)
            
    scripts = None
    
    # 1. Try Gemini API
    if config.GEMINI_API_KEY:
        try:
            print(f"[*] Đang gửi yêu cầu tới Google Gemini ({config.GEMINI_MODEL}) để viết kịch bản...")
            scripts = generate_script_gemini(input_data, config.GEMINI_API_KEY)
            print(f"[✓] Google Gemini đã tạo kịch bản sư phạm thành công cho {len(scripts)} slides!")
        except Exception as e:
            print(f"[!] Lỗi khi gọi Gemini API: {e}")
            
    # 2. Try OpenAI API
    if scripts is None and config.OPENAI_API_KEY:
        try:
            print(f"[*] Đang gửi yêu cầu tới OpenAI ({config.OPENAI_MODEL}) để viết kịch bản...")
            scripts = generate_script_openai(input_data, config.OPENAI_API_KEY)
            print(f"[✓] OpenAI đã tạo kịch bản sư phạm thành công cho {len(scripts)} slides!")
        except Exception as e:
            print(f"[!] Lỗi khi gọi OpenAI API: {e}")
            
    # 3. Smart Rich Offline Script Generator
    if scripts is None:
        print("[!] Không tìm thấy API Key Gemini/OpenAI hợp lệ. Đang kích hoạt bộ sinh kịch bản sư phạm chuyên sâu Offline.")
        scripts = generate_rich_offline_script(input_data)
        
    # Save script.json
    output_script_file = config.WORKSPACE_DIR / "script.json"
    with open(output_script_file, "w", encoding="utf-8") as f:
        json.dump(scripts, f, ensure_ascii=False, indent=2)
        
    print(f"[✓] Hoàn thành Bước 2. Kịch bản bài học đã lưu tại: {output_script_file}\n")
    for item in scripts:
        print(f"   📖 [Slide {item['slide_index']} - {item['title']}]:")
        print(f"      \"{item['script'][:140]}...\"\n")
        
    return scripts

if __name__ == "__main__":
    run_step2()
