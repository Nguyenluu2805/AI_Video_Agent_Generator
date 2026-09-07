import os
import sys
import json
from pathlib import Path
from pptx import Presentation
from PIL import Image, ImageDraw, ImageFont

# Add parent directory to sys.path for config import
sys.path.insert(0, str(Path(__file__).resolve().parent))
import config

def extract_text_and_notes(pptx_path: Path) -> list:
    """
    Extract slide titles, bullet points, text blocks, and speaker notes from PPTX.
    """
    prs = Presentation(str(pptx_path))
    slides_data = []
    
    for idx, slide in enumerate(prs.slides, start=1):
        title = ""
        bullet_points = []
        notes = ""
        
        # 1. Extract Slide Title and Text Shapes
        for shape in slide.shapes:
            if shape.has_text_frame:
                text_frame = shape.text_frame
                text = text_frame.text.strip()
                if not text:
                    continue
                
                # Check if it is the title shape
                if shape == slide.shapes.title or (not title and len(text) < 120 and "\n" not in text):
                    title = text
                else:
                    for paragraph in text_frame.paragraphs:
                        p_text = paragraph.text.strip()
                        if p_text and p_text not in bullet_points:
                            bullet_points.append(p_text)
            
            # Check for tables
            if shape.has_table:
                for row in shape.table.rows:
                    row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                    if row_text:
                        bullet_points.append(f"Bảng dữ liệu: {row_text}")
        
        # 2. Extract Speaker Notes (Ghi chú của người thuyết trình)
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
            notes = slide.notes_slide.notes_text_frame.text.strip()
            # Clean default PowerPoint template note lines if any
            if "Click to add notes" in notes:
                notes = ""
        
        if not title:
            title = f"Slide {idx}"
            
        slides_data.append({
            "slide_index": idx,
            "title": title,
            "bullet_points": bullet_points,
            "speaker_notes": notes,
            "image_path": str(config.IMAGES_DIR / f"slide_{idx:03d}.png")
        })
        
    return slides_data

def export_slides_as_images(pptx_path: Path, output_dir: Path, total_slides: int) -> bool:
    """
    Export all slides from PPTX to PNG images using Microsoft PowerPoint (via win32com).
    Falls back to Pillow image generator if PowerPoint COM is not accessible.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    abs_pptx = str(pptx_path.resolve())
    
    # Try PowerPoint COM first
    try:
        import win32com.client
        import pythoncom
        
        pythoncom.CoInitialize()
        powerpoint = win32com.client.Dispatch("PowerPoint.Application")
        # Do not force visible window
        try:
            powerpoint.Visible = 1  # PowerPoint COM often requires 1 in win32com
        except Exception:
            pass
            
        deck = powerpoint.Presentations.Open(abs_pptx, ReadOnly=True, Untitled=False, WithWindow=False)
        print(f"[*] Exporting {deck.Slides.Count} slides using PowerPoint...")
        
        for i, slide in enumerate(deck.Slides, start=1):
            image_dest = output_dir / f"slide_{i:03d}.png"
            slide.Export(str(image_dest.resolve()), "PNG", config.VIDEO_WIDTH, config.VIDEO_HEIGHT)
            print(f"    -> Exported: slide_{i:03d}.png")
            
        deck.Close()
        powerpoint.Quit()
        pythoncom.CoUninitialize()
        return True
    except Exception as e:
        print(f"[!] Warning: PowerPoint COM export failed ({e}). Generating high-quality fallback slide cards...")
        
    # Fallback: Generate visually clean slide cards using Pillow
    prs = Presentation(str(pptx_path))
    for i, slide_data in enumerate(prs.slides, start=1):
        image_dest = output_dir / f"slide_{i:03d}.png"
        img = Image.new("RGB", (config.VIDEO_WIDTH, config.VIDEO_HEIGHT), color=(24, 28, 36))
        draw = ImageDraw.Draw(img)
        
        # Header banner
        draw.rectangle([(0, 0), (config.VIDEO_WIDTH, 120)], fill=(30, 41, 59))
        draw.rectangle([(0, 116), (config.VIDEO_WIDTH, 120)], fill=(59, 130, 246))
        
        # Card background
        draw.rounded_rectangle([(80, 180), (config.VIDEO_WIDTH - 80, config.VIDEO_HEIGHT - 80)], radius=20, fill=(33, 41, 54), outline=(51, 65, 85), width=2)
        
        title_text = f"Slide {i}"
        for shape in slide_data.shapes:
            if shape.has_text_frame and shape.text_frame.text.strip():
                title_text = shape.text_frame.text.strip().split("\n")[0][:80]
                break
                
        # Draw slide number and title
        draw.text((100, 45), f"BÀI GIẢNG ĐIỆN TỬ  |  TRANG {i}", fill=(148, 163, 184))
        draw.text((120, 220), title_text, fill=(255, 255, 255))
        
        img.save(image_dest)
        print(f"    -> Generated fallback image: slide_{i:03d}.png")
        
    return True

def run_step1(pptx_file: Path) -> list:
    """
    Main function for Step 1: PPTX Extractor
    """
    print(f"\n=======================================================")
    print(f"[Bước 1/5] Trích xuất Dữ liệu từ file: {pptx_file.name}")
    print(f"=======================================================")
    
    if not pptx_file.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {pptx_file}")
        
    # 1. Extract content & notes
    slides_data = extract_text_and_notes(pptx_file)
    print(f"[*] Đã trích xuất nội dung text và ghi chú của {len(slides_data)} slides.")
    
    # 2. Export images
    export_slides_as_images(pptx_file, config.IMAGES_DIR, len(slides_data))
    
    # 3. Save extracted JSON
    output_json = config.WORKSPACE_DIR / "extracted_data.json"
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(slides_data, f, ensure_ascii=False, indent=2)
        
    print(f"[✓] Hoàn thành Bước 1. Dữ liệu đã lưu tại: {output_json}")
    return slides_data

if __name__ == "__main__":
    test_pptx = config.INPUT_DIR / "demo_lecture.pptx"
    if test_pptx.exists():
        run_step1(test_pptx)
    else:
        print(f"File {test_pptx} chưa tồn tại. Vui lòng tạo file mẫu để test.")
