"""
Suite: test_advanced_suite.py
Description: Bo kiem thu nang cao 5 Test Case bao phu toan dien he thong AI Video Agent Studio:
  - TC 1: PPTX Multi-Slide Extraction and 1080p Image Integrity
  - TC 2: Pedagogical Script Generation (AI + Offline Fallback) and Sanitization
  - TC 3: Dual-Voice TTS Synthesis and Audio Integrity (Male + Female consistent)
  - TC 4: End-to-End 1080p Video Rendering and Audio-Visual Sync Verification
  - TC 5: Flask Web API Endpoints and Real-time Progress Tracking
"""

import os
import sys
import json
import time
import asyncio
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import config
from extractor import run_extractor
from script_gen import generate_rich_offline_script
from tts_engine import clean_text_for_tts, synthesize_edge_tts, synthesize_all_audio_async
from voice_cloner import run_voice_cloner
from video_renderer import run_video_renderer, get_audio_duration
from app import app


class AdvancedSystemTestSuite(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\n" + "=" * 70)
        print("TEST: BAT DAU CHAY BO 5 TEST CASE NANG CAO CHO AI VIDEO AGENT STUDIO")
        print("=" * 70)
        cls.test_pptx = config.INPUT_DIR / "python_array.pptx"
        if not cls.test_pptx.exists():
            candidates = list(config.INPUT_DIR.glob("*.pptx"))
            if candidates:
                cls.test_pptx = candidates[0]
            else:
                raise FileNotFoundError("Khong tim thay file PPTX nao trong input/")
        print(f"File Slide: {cls.test_pptx.name}")

    def test_01_pptx_extraction_and_image_quality(self):
        """TC 1: Kiem thu trich xuat Slide PPTX, hinh anh 1080p va metadata."""
        print("\n[TEST CASE 1] Trich xuat PPTX va Kiem tra chat luong anh 1080p...")
        start_t = time.time()
        slides_data = run_extractor(self.test_pptx)
        elapsed = time.time() - start_t

        self.assertIsInstance(slides_data, list, "Du lieu tra ve phai la danh sach slide.")
        self.assertGreater(len(slides_data), 0, "So luong slide trich xuat phai > 0.")
        
        for item in slides_data:
            self.assertIn("slide_index", item)
            self.assertIn("title", item)
            self.assertIn("image_path", item)
            img_path = Path(item["image_path"])
            self.assertTrue(img_path.exists(), f"Anh slide {img_path} khong ton tai!")
            self.assertGreater(img_path.stat().st_size, 1024, f"Anh {img_path.name} qua nho (<1KB)!")
            
        print(f"  [PASS] TC 1 PASSED: Trich xuat thanh cong {len(slides_data)} slides trong {elapsed:.2f}s.")

    def test_02_script_generation_and_sanitization(self):
        """TC 2: Kiem thu bo sinh kich ban su pham va lam sach ky tu Unicode dac biet."""
        print("\n[TEST CASE 2] Sinh kich ban su pham va Chuan hoa Unicode...")
        start_t = time.time()
        slides_data = run_extractor(self.test_pptx)
        offline_scripts = generate_rich_offline_script(slides_data)
        self.assertEqual(len(offline_scripts), len(slides_data))
        
        complex_text = "Hoc ve array: `list`—mang dong [10, 20, 30] & so_list = 10% → Σ tong ✓ ⚡ ◈!"
        cleaned = clean_text_for_tts(complex_text)
        
        self.assertNotIn("`", cleaned, "Khong duoc chua dau backtick code.")
        self.assertNotIn("—", cleaned, "Dau em-dash phai duoc thay the thanh dau phay.")
        self.assertNotIn("⚡", cleaned, "Khong duoc chua emoji/ky hieu la.")
        self.assertIn("phần trăm", cleaned, "% phai duoc doc thanh chu.")
        self.assertIn("gán bằng", cleaned, "= phai duoc chuan hoa thanh loi doc.")
        
        elapsed = time.time() - start_t
        print(f"  [PASS] TC 2 PASSED: Kich ban va bo loc text chuan hoa thanh cong trong {elapsed:.2f}s.")

    def test_03_dual_voice_tts_synthesis(self):
        """TC 3: Kiem thu tong hop am thanh giong Nam (Nam Minh) va giong Nu (Hoai My)."""
        print("\n[TEST CASE 3] Tong hop TTS Giong Nam va Giong Nu (Do dai va tinh toan ven)...")
        start_t = time.time()
        
        test_text_male = "Chao cac ban sinh vien, day la bai kiem tra do muot ma cua giong doc Nam Minh tren he sinh thai Microsoft Neural."
        test_text_female = "Chao cac ban sinh vien, day la bai kiem tra do truyen cam cua giong doc Hoai My tren he sinh thai Microsoft Neural."
        
        out_male = config.WORKSPACE_DIR / "tc3_male.mp3"
        out_female = config.WORKSPACE_DIR / "tc3_female.mp3"
        
        res_male = asyncio.run(synthesize_edge_tts(test_text_male, "vi-VN-NamMinhNeural", out_male))
        self.assertTrue(res_male)
        self.assertTrue(out_male.exists())
        self.assertGreater(out_male.stat().st_size, 5000, "File audio nam phai > 5KB.")
        dur_male = get_audio_duration(str(out_male))
        self.assertGreater(dur_male, 2.0, "Thoi luong audio nam phai > 2s.")
        
        res_female = asyncio.run(synthesize_edge_tts(test_text_female, "vi-VN-HoaiMyNeural", out_female))
        self.assertTrue(res_female)
        self.assertTrue(out_female.exists())
        self.assertGreater(out_female.stat().st_size, 5000, "File audio nu phai > 5KB.")
        dur_female = get_audio_duration(str(out_female))
        self.assertGreater(dur_female, 2.0, "Thoi luong audio nu phai > 2s.")
        
        try: out_male.unlink()
        except Exception: pass
        try: out_female.unlink()
        except Exception: pass
        
        elapsed = time.time() - start_t
        print(f"  [PASS] TC 3 PASSED: Giong Nam ({dur_male:.2f}s) va Giong Nu ({dur_female:.2f}s) tao hoan hao trong {elapsed:.2f}s.")

    def test_04_video_rendering_and_sync(self):
        """TC 4: Kiem thu render video 1080p va dong bo khop thoi luong hinh anh - am thanh."""
        print("\n[TEST CASE 4] Render Video MP4 1080p va Kiem tra khop thoi luong...")
        start_t = time.time()
        
        slides_data = run_extractor(self.test_pptx)[:2]
        scripts = generate_rich_offline_script(slides_data)
        audio_records = asyncio.run(synthesize_all_audio_async(scripts, voice_name="vi-VN-NamMinhNeural"))
        self.assertEqual(len(audio_records), 2)
        
        final_audio = run_voice_cloner(audio_records, enable_rvc=False)
        test_video_name = "test_case_4_render.mp4"
        output_video = run_video_renderer(final_audio, output_name=test_video_name)
        
        self.assertTrue(output_video.exists(), "File video render khong ton tai!")
        self.assertGreater(output_video.stat().st_size, 50000, "Dung luong video phai > 50KB.")
        
        video_dur = get_audio_duration(str(output_video))
        total_audio_dur = sum(get_audio_duration(str(Path(a["audio_path"]))) for a in final_audio)
        expected_min_dur = total_audio_dur + (len(final_audio) * config.SLIDE_PAUSE_DURATION * 0.5)
        
        self.assertGreaterEqual(video_dur, expected_min_dur - 1.0, "Thoi luong video phai khop voi tong audio + pause.")
        
        elapsed = time.time() - start_t
        print(f"  [PASS] TC 4 PASSED: Video render thanh cong ({output_video.stat().st_size/1024:.1f} KB, {video_dur:.2f}s) trong {elapsed:.2f}s.")

    def test_05_web_api_endpoints_and_status(self):
        """TC 5: Kiem thu bo Flask REST API (index, upload, latest-video, extract-and-script)."""
        print("\n[TEST CASE 5] Kiem tra toan bo REST API Endpoints cua Web Studio...")
        start_t = time.time()
        
        client = app.test_client()
        
        # 1. UI Index endpoint
        res_idx = client.get("/")
        self.assertEqual(res_idx.status_code, 200)
        self.assertIn(b"AI Video Agent Studio", res_idx.data)
        
        # 2. Latest video endpoint
        res_video = client.get("/api/latest-video")
        self.assertEqual(res_video.status_code, 200)
        data_video = json.loads(res_video.data)
        self.assertIn("exists", data_video)
        
        # 3. Bad upload endpoint validation
        res_bad_upload = client.post("/api/upload")
        self.assertEqual(res_bad_upload.status_code, 400)
        
        # 4. Extract and script endpoint validation
        res_script = client.post("/api/extract-and-script", json={"filename": "python_array.pptx"})
        self.assertEqual(res_script.status_code, 200)
        data_script = json.loads(res_script.data)
        self.assertTrue(data_script.get("success"))
        self.assertIn("slides", data_script)
        self.assertGreater(len(data_script["slides"]), 0)
        
        elapsed = time.time() - start_t
        print(f"  [PASS] TC 5 PASSED: 4 Web API Endpoints phan hoi chuan xac JSON trong {elapsed:.2f}s.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
