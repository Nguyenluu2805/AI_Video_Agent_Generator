import os
import sys
import json
import subprocess
from pathlib import Path

# Add parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import config

def get_audio_duration_ffmpeg(audio_path: str) -> float:
    """Get exact duration of an audio file using imageio-ffmpeg."""
    import imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    cmd = [
        ffmpeg_exe, "-i", audio_path
    ]
    result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, errors="ignore")
    # Parse Duration: 00:00:12.34
    import re
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", result.stderr)
    if match:
        hours = float(match.group(1))
        minutes = float(match.group(2))
        seconds = float(match.group(3))
        return hours * 3600 + minutes * 60 + seconds
    return 5.0

def assemble_video_ffmpeg(slide_items: list, output_video_path: Path) -> bool:
    """
    Direct ultra-fast and reliable Video Assembler using FFmpeg binary.
    Combines slide PNGs and audio files with seamless transitions.
    """
    import imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    temp_clips = []
    temp_dir = config.WORKSPACE_DIR / "temp_clips"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"[*] Đang xử lý {len(slide_items)} đoạn video cho từng slide...")
    
    for i, item in enumerate(slide_items, start=1):
        img_path = item["image_path"]
        audio_path = item["audio_path"]
        duration = get_audio_duration_ffmpeg(audio_path) + config.SLIDE_PAUSE_DURATION
        
        clip_path = temp_dir / f"clip_{i:03d}.mp4"
        temp_clips.append(clip_path)
        
        # Command to create static image video with audio and pad audio with silence
        # -loop 1 -i image -i audio -c:v libx264 -tune stillimage -c:a aac -b:a 192k -pix_fmt yuv420p -t duration
        cmd = [
            ffmpeg_exe, "-y",
            "-loop", "1",
            "-i", img_path,
            "-i", audio_path,
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-vf", f"scale={config.VIDEO_WIDTH}:{config.VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={config.VIDEO_WIDTH}:{config.VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2",
            "-t", str(duration),
            "-shortest",
            str(clip_path.resolve())
        ]
        
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print(f"    -> Render xong Slide {i} ({duration:.1f}s)")
        
    # Create concat list file
    concat_list_file = temp_dir / "concat_list.txt"
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for clip in temp_clips:
            # Escape single quotes and use forward slashes for ffmpeg concat
            f_path = str(clip.resolve()).replace("\\", "/")
            f.write(f"file '{f_path}'\n")
            
    print(f"[*] Đang nối tất cả các slide thành video hoàn chỉnh: {output_video_path.name}...")
    concat_cmd = [
        ffmpeg_exe, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list_file.resolve()),
        "-c", "copy",
        str(output_video_path.resolve())
    ]
    subprocess.run(concat_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    
    return True

def run_step5(slide_items: list = None, output_name: str = "output_video.mp4") -> Path:
    """
    Main function for Step 5: Video Assembler
    """
    print(f"\n=======================================================")
    print(f"[Bước 5/5] Lắp Ráp Video Bài Giảng Cuối Cùng (.mp4)")
    print(f"=======================================================")
    
    if slide_items is None:
        final_meta = config.WORKSPACE_DIR / "final_audio_meta.json"
        if not final_meta.exists():
            raise FileNotFoundError(f"Chưa có file {final_meta}. Vui lòng chạy các bước trước.")
        with open(final_meta, "r", encoding="utf-8") as f:
            slide_items = json.load(f)
            
    output_video_path = config.OUTPUT_DIR / output_name
    
    try:
        assemble_video_ffmpeg(slide_items, output_video_path)
    except Exception as e:
        print(f"[!] Lỗi khi render video bằng FFmpeg: {e}")
        raise e
        
    print(f"\n🎉 [THÀNH CÔNG] Video bài giảng đã được tạo hoàn tất!")
    print(f"📍 Đường dẫn file: {output_video_path.resolve()}")
    if output_video_path.exists():
        size_mb = output_video_path.stat().st_size / (1024 * 1024)
        print(f"📦 Kích thước file: {size_mb:.2f} MB")
        
    return output_video_path

if __name__ == "__main__":
    run_step5()
