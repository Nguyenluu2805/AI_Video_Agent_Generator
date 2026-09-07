import os
import sys
import subprocess
from pathlib import Path
import imageio_ffmpeg

# Add parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import config

VOICE_SAMPLES_DIR = config.PROJECT_ROOT / "voice_samples"
VOICE_SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

def extract_audio_from_video(video_path: Path, output_wav: Path = None) -> Path:
    """
    Extract clean 44.1kHz mono WAV audio from any input video or audio file.
    """
    if output_wav is None:
        output_wav = VOICE_SAMPLES_DIR / "my_voice_sample.wav"
        
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    print(f"[*] Đang trích xuất giọng nói từ video: {video_path.name}...")
    cmd = [
        ffmpeg_exe, "-y",
        "-i", str(video_path.resolve()),
        "-vn", # Bỏ video, chỉ lấy audio
        "-acodec", "pcm_s16le", # PCM 16-bit
        "-ar", "44100", # Tần số lấy mẫu 44.1kHz chuẩn RVC
        "-ac", "1", # Mono (chuẩn cho training/cloning)
        str(output_wav.resolve())
    ]
    
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"[✓] Đã trích xuất thành công file âm thanh giọng nói: {output_wav.name}")
    print(f"    -> Vị trí lưu: {output_wav.resolve()}")
    return output_wav

if __name__ == "__main__":
    if len(sys.argv) > 1:
        v_path = Path(sys.argv[1])
        if v_path.exists():
            extract_audio_from_video(v_path)
        else:
            print(f"[!] Không tìm thấy file: {v_path}")
    else:
        # Check if there are any video files in voice_samples/
        videos = list(VOICE_SAMPLES_DIR.glob("*.mp4")) + list(VOICE_SAMPLES_DIR.glob("*.mov")) + list(VOICE_SAMPLES_DIR.glob("*.mkv"))
        if videos:
            extract_audio_from_video(videos[0])
        else:
            print(f"Vui lòng copy file video có giọng của bạn vào: {VOICE_SAMPLES_DIR}")
