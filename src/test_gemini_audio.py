import os
import io
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

text_to_speak = "Chào mừng tất cả các bạn học viên đã quay trở lại với bài học Product Backlog và User Story trong mô hình Scrum! Hôm nay chúng ta sẽ cùng tìm hiểu về tiêu chí INVEST và biểu đồ Burndown Chart trên Trello."

out_dir = Path("voice_samples")
out_dir.mkdir(parents=True, exist_ok=True)

for voice_name in ["Puck", "Charon", "Kore", "Fenrir"]:
    print(f"Generating Gemini Native Multilingual Speech with voice {voice_name}...")
    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=f"Đọc to nội dung sau bằng tiếng Việt với phong cách giảng dạy cuốn hút, các từ tiếng Anh phát âm chuẩn bản xứ Mỹ: \"{text_to_speak}\"",
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice_name
                        )
                    )
                )
            )
        )
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                raw_pcm = part.inline_data.data
                raw_path = out_dir / f"gemini_{voice_name.lower()}_temp.pcm"
                raw_path.write_bytes(raw_pcm)
                
                mp3_path = out_dir / f"gemini_voice_{voice_name.lower()}.mp3"
                # Convert PCM 24kHz to MP3 192k
                subprocess.run([
                    "ffmpeg", "-y", "-f", "s16le", "-ar", "24000", "-ac", "1",
                    "-i", str(raw_path.resolve()),
                    "-c:a", "libmp3lame", "-b:a", "192k",
                    str(mp3_path.resolve())
                ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                if raw_path.exists():
                    raw_path.unlink()
                    
                print(f"  -> [✓] Generated {mp3_path.name} ({round(mp3_path.stat().st_size/1024, 1)} KB)")
                break
    except Exception as e:
        print(f"  -> Error with {voice_name}:", e)

print("\nDone generating Gemini native audio samples!")
