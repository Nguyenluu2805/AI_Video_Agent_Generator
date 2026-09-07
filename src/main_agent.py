import os
import sys
import argparse
import time
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import config
from step1_extractor import run_step1
from step2_llm import run_step2
from step3_tts import run_step3
from step4_rvc import run_step4
from step5_video import run_step5

console = Console()

def print_banner():
    banner_text = """[bold cyan]╔══════════════════════════════════════════════════════════════════╗
║               🎬 AI LECTURE VIDEO AGENT PIPELINE                 ║
║   Chuyển đổi Slide PowerPoint thành Video Giảng Dạy Tự Động     ║
║             Hỗ trợ AI Scripting & RVC Voice Cloning              ║
╚══════════════════════════════════════════════════════════════════╝[/bold cyan]"""
    console.print(banner_text)

def run_pipeline(pptx_path: Path, enable_rvc: bool = False, output_filename: str = "output_video.mp4"):
    start_time = time.time()
    print_banner()
    
    table = Table(title="📋 Cấu Hình Chạy Pipeline", show_header=True, header_style="bold magenta")
    table.add_column("Tham số", style="dim", width=25)
    table.add_column("Giá trị", style="green")
    
    table.add_row("File PowerPoint Đầu Vào", str(pptx_path))
    table.add_row("LLM Provider", f"{config.LLM_PROVIDER.upper()} ({'Có API Key' if config.GEMINI_API_KEY or config.OPENAI_API_KEY else 'Dùng bộ tạo offline'})")
    table.add_row("Giọng Đọc Nền (TTS)", config.TTS_VOICE)
    table.add_row("Voice Cloning (RVC GPU)", "BẬT (RTX 3060 Ti)" if enable_rvc else "TẮT (Dùng giọng Edge-TTS)")
    table.add_row("File Video Đầu Ra", str(config.OUTPUT_DIR / output_filename))
    
    console.print(table)
    console.print("\n[bold yellow]🚀 Bắt đầu quá trình tạo video tự động...[/bold yellow]\n")
    
    # Step 1: PPTX Extractor
    slides_data = run_step1(pptx_path)
    
    # Step 2: LLM Script Writer
    scripts = run_step2(slides_data)
    
    # Step 3: Base TTS
    base_audio_records = run_step3(scripts)
    
    # Step 4: Voice Cloning (RVC)
    final_records = run_step4(base_audio_records, enable_rvc=enable_rvc)
    
    # Step 5: Video Assembler
    output_video = run_step5(final_records, output_name=output_filename)
    
    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    
    console.print(Panel(
        f"[bold green]✨ TOÀN BỘ QUY TRÌNH ĐÃ HOÀN TẤT THÀNH CÔNG! ✨[/bold green]\n\n"
        f"⏱  [bold]Tổng thời gian thực hiện:[/bold] {minutes} phút {seconds} giây\n"
        f"📁 [bold]File Video bài giảng hoàn chỉnh:[/bold] [underline cyan]{output_video.resolve()}[/underline cyan]\n"
        f"💡 Bạn có thể mở trực tiếp file video trên để thưởng thức bài giảng!",
        title="🎉 Kết Quả",
        border_style="green"
    ))
    return output_video

def main():
    parser = argparse.ArgumentParser(description="AI Video Lecture Agent - Biến PPTX thành Video Bài Giảng")
    parser.add_argument("--input", "-i", type=str, default="", help="Đường dẫn tới file PowerPoint .pptx")
    parser.add_argument("--enable-rvc", action="store_true", help="Bật tính năng nhái giọng RVC bằng GPU")
    parser.add_argument("--output", "-o", type=str, default="output_video.mp4", help="Tên file video đầu ra (.mp4)")
    parser.add_argument("--voice", type=str, default="", help="Tùy chọn giọng Edge-TTS (vd: vi-VN-HoaiMyNeural hoặc vi-VN-NamMinhNeural)")
    
    args = parser.parse_args()
    
    if args.voice:
        config.TTS_VOICE = args.voice
        
    pptx_path = None
    if args.input:
        pptx_path = Path(args.input)
    else:
        # Check if default demo presentation exists in input/
        default_pptx = config.INPUT_DIR / "demo_lecture.pptx"
        if default_pptx.exists():
            pptx_path = default_pptx
        else:
            # Check any pptx in input/
            pptx_files = list(config.INPUT_DIR.glob("*.pptx"))
            if pptx_files:
                pptx_path = pptx_files[0]
            else:
                console.print("[bold red][!] Không tìm thấy file .pptx trong thư mục input/. Vui lòng copy file .pptx vào thư mục input/ hoặc chỉ định bằng --input path/to/file.pptx[/bold red]")
                sys.exit(1)
                
    if not pptx_path.exists():
        console.print(f"[bold red][!] File không tồn tại: {pptx_path}[/bold red]")
        sys.exit(1)
        
    run_pipeline(pptx_path, enable_rvc=args.enable_rvc, output_filename=args.output)

if __name__ == "__main__":
    main()
