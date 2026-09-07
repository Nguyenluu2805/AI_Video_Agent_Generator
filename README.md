# 🎬 AI Video Agent Generator Studio (v2.0 PRO)

Hệ thống **AI Agent tự động hóa toàn diện quy trình chuyển đổi bài giảng PowerPoint (`.pptx`) thành Video bài giảng chất lượng cao 1080p (`.mp4`)**. Tích hợp kịch bản sư phạm tự nhiên (Google Gemini / OpenAI / Offline Engine), lồng tiếng song ngữ Việt - Anh đa dạng (Microsoft Neural TTS / EverAI Multilingual API), tùy chọn Voice Cloning RVC trên GPU và Web Studio Dark SaaS hiện đại.

---

## ✨ Tính Năng Nổi Bật

1. **Trích xuất Slide Tự Động (`src/extractor.py`)**:
   - Trích xuất toàn bộ slide thành hình ảnh 1080p Full HD sắc nét bằng PowerPoint COM API (kèm bộ vẽ Slide Card dự phòng).
   - Thu thập tiêu đề, nội dung gạch đầu dòng, bảng biểu và Speaker Notes (Ghi chú diễn giả).

2. **Kịch Bản Sư Phạm Diễn Thuyết (`src/script_gen.py`)**:
   - Ứng dụng Google Gemini / OpenAI để chuyển đổi văn bản thô thành lời giảng sư phạm lôi cuốn.
   - Nghệ thuật dấu câu tạo nhịp điệu (Prosody Punctuation) với câu hỏi gợi mở, ngắt nghỉ tự nhiên như giảng viên trực tiếp.
   - Tự động kích hoạt bộ sinh kịch bản sư phạm chuyên sâu Offline khi không có kết nối internet hoặc API Key.

3. **Phòng Thu Lồng Tiếng Đa Năng (`src/tts_engine.py`)**:
   - **Microsoft Edge Neural TTS**: Giọng *Nam Minh* (Trầm ấm, chuẩn giảng dạy) & *Hoài My* (Truyền cảm, rõ ràng).
   - **EverAI Multilingual API**: Hỗ trợ thuật ngữ tiếng Anh tự nhiên và tích hợp Giọng Clone cá nhân hóa (*Nguyên*).

4. **Chuyển Đổi Âm Sắc & Voice Cloning (`src/voice_cloner.py`, `src/voice_utils.py`)**:
   - Tự động trích xuất âm thanh sạch từ video bài giảng cũ (.mp4, .mov, .wav) để học chất giọng người dùng.
   - Tùy chọn chuyển đổi âm sắc nơ-ron qua RVC V2 GPU RTX 3060 Ti.

5. **Lắp Ráp Video Tự Động (`src/video_renderer.py`)**:
   - Tự động đo thời lượng audio từng slide, căn khớp thời lượng slide 100% và xuất file MP4 chuẩn H.264/AAC.

6. **Web Studio Hiện Đại & Hệ Thống Toast Thông Báo (`app.py`, `templates/index.html`)**:
   - Giao diện Dark SaaS phong cách AI Studio (Glassmorphism).
   - **Hệ thống Toast Notification động**: Thông báo trạng thái thời gian thực (*Success, Info, Warning, Error*), không dùng alert pop-up.
   - **Bộ Icon SVG Vector độc lập**: Nhúng trực tiếp, tải tức thì 0ms, không phụ thuộc font CDN bên ngoài.
   - **Trình chỉnh sửa kịch bản đa slide**: Xem trước hình ảnh và tùy biến lời giảng trước khi render video.

---

## 📁 Cấu Trúc Dự Án Chuẩn Hóa

```
AI_Video_Agent/
├── app.py                     # Web Studio Server (Flask + SSE Streaming)
├── run_cli.py                 # Trình chạy dòng lệnh CLI nhanh
├── config.py                  # Cấu hình tập trung toàn hệ thống
├── requirements.txt           # Danh sách thư viện Python
├── .env.example               # Mẫu cấu hình API Keys & tham số
├── README.md                  # Hướng dẫn chi tiết
│
├── src/                       # Các module xử lý lõi (Clean Architecture)
│   ├── __init__.py            # Khởi tạo package
│   ├── extractor.py           # Bước 1: Trích xuất PPTX & ảnh 1080p
│   ├── script_gen.py          # Bước 2: Sinh kịch bản sư phạm AI
│   ├── tts_engine.py          # Bước 3: Microsoft EdgeTTS & EverAI Studio
│   ├── voice_cloner.py        # Bước 4: Voice Cloning RVC & Bộ lọc âm sắc
│   ├── video_renderer.py      # Bước 5: Render & nối video FFmpeg 1080p
│   ├── voice_utils.py         # Tiện ích trích xuất giọng sạch từ video
│   └── pipeline.py            # Orchestrator điều phối toàn bộ quy trình
│
├── templates/
│   └── index.html             # Giao diện Web Studio (SVG Icons & Toasts)
├── voice_samples/             # Thư mục chứa mẫu giọng thật (.wav)
├── workspace/                 # Dữ liệu đệm xử lý trung gian (gitignored)
└── output/                    # Video bài giảng thành phẩm (.mp4)
```

---

## 🚀 Hướng Dẫn Cài Đặt & Sử Dụng

### 1. Cài đặt thư viện phụ thuộc
```bash
pip install -r requirements.txt
```

### 2. Cấu hình biến môi trường (Tùy chọn)
Tạo file `.env` từ `.env.example`:
```env
GEMINI_API_KEY=your_gemini_api_key
EVERAI_API_KEY=your_everai_api_key
TTS_VOICE=vi-VN-NamMinhNeural
TTS_RATE=-4%
```

### 3. Khởi chạy Web Studio
```bash
python app.py
```
👉 Mở trình duyệt tại địa chỉ: **`http://127.0.0.1:5000`**

### 4. Khởi chạy qua dòng lệnh CLI
```bash
python run_cli.py --input "input/your_presentation.pptx" --voice "vi-VN-NamMinhNeural" --output "output_video.mp4"
```

---

## 📜 Giấy Phép & Tác Quyền
Dự án được phát triển nhằm mục đích tự động hóa sản xuất nội dung bài giảng số chất lượng cao phục vụ giáo dục và đào tạo.
