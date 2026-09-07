# 🎬 AI Lecture Video Agent

Hệ thống **AI Agent tự động hóa 100% quy trình chuyển đổi bài giảng PowerPoint (`.pptx`) thành Video bài giảng Full HD (`.mp4`)** với kịch bản sư phạm truyền cảm (Google Gemini / OpenAI), lồng tiếng song ngữ Việt - Anh mượt mà (Microsoft Neural / EverAI / RVC Voice Cloning), cùng giao diện Web Studio trực quan.

---

## ✨ Tính Năng Nổi Bật

1. **Trích xuất Slide Tự Động (`src/step1_extractor.py`)**:
   - Trích xuất toàn bộ slide thành hình ảnh 1080p Full HD sắc nét bằng PowerPoint COM API.
   - Thu thập tiêu đề, nội dung gạch đầu dòng và Speaker Notes (Ghi chú diễn giả).
2. **Kịch Bản Sư Phạm Diễn Thuyết (`src/step2_llm.py`)**:
   - Ứng dụng Google Gemini 3.6 Flash / OpenAI GPT-4o để chuyển đổi văn bản thô thành lời giảng sư phạm lôi cuốn.
   - Kỹ thuật dấu câu tạo nhịp điệu (Prosody Punctuation) với câu hỏi gợi mở, ngắt nghỉ tự nhiên.
3. **Phòng Thu Lồng Tiếng Đa Dạng (`src/step3_tts.py`, `src/everai_tts.py`)**:
   - Hỗ trợ Microsoft Edge-TTS Studio (Nam Minh / Hoài My) với tốc độ tinh chỉnh `-4%`.
   - Hỗ trợ tích hợp EverAI Multilingual (`everai-v1.6`) với giọng Clone cá nhân hóa.
4. **Voice Cloning Cá Nhân Hóa (`src/step4_rvc.py`)**:
   - Tích hợp Retrieval-based Voice Conversion (RVC V2) tăng tốc bằng GPU NVIDIA RTX.
5. **Lắp Ráp Video Tự Động (`src/step5_video.py`)**:
   - Tự động đo độ dài âm thanh từng slide, căn khớp thời lượng slide 100% và xuất file MP4 chuẩn H.264/AAC.
6. **Web Studio Dashboard (`app.py`)**:
   - Giao diện Web trực quan để tải lên slide, chỉnh sửa kịch bản, nghe thử âm thanh và theo dõi tiến độ render thời gian thực.

---

## 📁 Cấu Trúc Dự Án

```
AI_Video_Agent/
├── input/                  # Chứa file PowerPoint (.pptx)
├── models/                 # Chứa model RVC (.pth, .index)
├── workspace/              # Dữ liệu trung gian (ảnh slide, audio)
├── output/                 # Video bài giảng thành phẩm (.mp4)
├── src/                    # Mã nguồn các module xử lý
│   ├── config.py           # Cấu hình tập trung
│   ├── step1_extractor.py  # Trích xuất slide & nội dung
│   ├── step2_llm.py        # Tạo kịch bản bài giảng bằng AI
│   ├── step3_tts.py        # Tổng hợp giọng đọc Neural TTS
│   ├── step4_rvc.py        # Voice Cloning RVC
│   ├── step5_video.py      # Lắp ráp video hoàn chỉnh
│   ├── everai_tts.py       # Tích hợp EverAI API
│   └── main_agent.py       # Pipeline Runner
├── templates/              # Giao diện HTML Web Studio
├── static/                 # CSS/JS cho Web Studio
├── app.py                  # Web Studio Server
├── .env.example            # Mẫu cấu hình biến môi trường
├── requirements.txt        # Danh sách thư viện Python
└── README.md
```

---

## 🚀 Hướng Dẫn Cài Đặt & Sử Dụng

### 1. Cài đặt môi trường
```bash
# Cài đặt các thư viện phụ thuộc
pip install -r requirements.txt
```

### 2. Cấu hình biến môi trường
Sao chép `.env.example` thành `.env` và điền các API Key:
```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key
TTS_ENGINE=edge-tts
TTS_VOICE=vi-VN-NamMinhNeural
TTS_RATE=-4%
```

### 3. Khởi động Web Studio
```bash
python app.py
```
👉 Mở trình duyệt tại địa chỉ: `http://127.0.0.1:5000`

### 4. Chạy trực tiếp qua CLI
```bash
python src/main_agent.py --input "input/your_presentation.pptx" --output "output_video.mp4"
```

---

## 📜 Giấy Phép
Dự án được phát triển cho mục đích giáo dục và tự động hóa sáng tạo nội dung bài giảng số.
