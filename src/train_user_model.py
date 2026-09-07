import os
import sys
import subprocess
import shutil
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RVC_ROOT = PROJECT_ROOT / "rvc_engine"
PYTHON_EXE = sys.executable

# Setup environment with PYTHONPATH
env = os.environ.copy()
env["PYTHONPATH"] = str(RVC_ROOT.resolve())

print("=======================================================")
print("=== BẮT ĐẦU HUẤN LUYỆN MÔ HÌNH NHÁI GIỌNG (RVC V2 GPU) ===")
print("=======================================================")

exp_name = "my_voice"
exp_dir = RVC_ROOT / "logs" / exp_name
exp_dir.mkdir(parents=True, exist_ok=True)
voice_samples_dir = PROJECT_ROOT / "voice_samples"

# 1. Preprocess audio
print(f"\n[1/4] Bước 1: Tiền xử lý & Cắt lát dữ liệu âm thanh...")
cmd1 = [
    PYTHON_EXE, "train/preprocess.py",
    str(voice_samples_dir.resolve()), "48000", "4",
    str(exp_dir.resolve()), "False", "3.7"
]
subprocess.run(cmd1, cwd=str(RVC_ROOT), env=env, check=True)
print("    [✓] Đã cắt lát và lọc âm thanh xong.")

# 2. Extract F0 (RMVPE) and HuBERT features
print(f"\n[2/4] Bước 2: Trích xuất Pitch RMVPE & HuBERT Features trên GPU RTX 3060 Ti...")
cmd2 = [
    PYTHON_EXE, "train/dataset/extract_f0.py",
    "cuda", "1", "0", "0",
    str(exp_dir.resolve()), "True"
]
subprocess.run(cmd2, cwd=str(RVC_ROOT), env=env, check=True)
print("    [✓] Trích xuất Pitch RMVPE hoàn tất.")

cmd3 = [
    PYTHON_EXE, "train/dataset/extract_hubert_feature.py",
    "cuda", "1", "0", "0",
    str(exp_dir.resolve()), "v2", "False"
]
subprocess.run(cmd3, cwd=str(RVC_ROOT), env=env, check=True)
print("    [✓] Trích xuất HuBERT Embeddings hoàn tất.")

# 3. Train neural network
print(f"\n[3/4] Bước 3: Huấn luyện Mạng Nơ-ron (30 Epochs trên GPU RTX 3060 Ti)...")
cmd4 = [
    PYTHON_EXE, "train/train.py",
    "-e", exp_name,
    "-sr", "48k",
    "-f0", "1",
    "-bs", "8",
    "-g", "0",
    "-te", "30",
    "-se", "10",
    "-pg", "assets/pretrained_v2/f0G48k.pth",
    "-pd", "assets/pretrained_v2/f0D48k.pth",
    "-l", "1",
    "-c", "0",
    "-sw", "0",
    "-v", "v2"
]
subprocess.run(cmd4, cwd=str(RVC_ROOT), env=env, check=True)
print("    [✓] Huấn luyện hoàn tất.")

# 4. Train Index
print(f"\n[4/4] Bước 4: Xây dựng Feature Index...")
cmd5 = [
    PYTHON_EXE, "train/train_index.py",
    str(exp_dir.resolve()), "v2"
]
subprocess.run(cmd5, cwd=str(RVC_ROOT), env=env, check=True)

# 5. Copy output models
output_models_dir = PROJECT_ROOT / "models"
output_models_dir.mkdir(parents=True, exist_ok=True)

# Find generated weights
pth_candidates = list((RVC_ROOT / "assets" / "weights").glob(f"*{exp_name}*.pth"))
if pth_candidates:
    shutil.copy2(pth_candidates[0], output_models_dir / "my_voice.pth")
    print(f"\n🎉 [THÀNH CÔNG] Đã lưu mô hình giọng nói tại: {output_models_dir / 'my_voice.pth'}")

index_candidates = list(exp_dir.glob("added_*.index"))
if index_candidates:
    shutil.copy2(index_candidates[0], output_models_dir / "my_voice.index")
    print(f"🎉 [THÀNH CÔNG] Đã lưu Index đặc trưng tại: {output_models_dir / 'my_voice.index'}")

print("\n=======================================================")
print("[✓] Mô hình Voice Cloning của bạn đã sẵn sàng sử dụng!")
print("=======================================================")
