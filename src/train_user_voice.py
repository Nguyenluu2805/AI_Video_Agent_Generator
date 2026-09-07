import os
import sys
import json
import random
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RVC_ROOT = PROJECT_ROOT / "rvc_engine"
PYTHON_EXE = sys.executable

exp_name = "my_voice"
exp_dir = RVC_ROOT / "logs" / exp_name
gt_wavs_dir = exp_dir / "0_gt_wavs"
feature_dir = exp_dir / "3_feature768"
f0_dir = exp_dir / "2a_f0"
f0nsf_dir = exp_dir / "2b-f0nsf"

print("=================================================================")
print("=== HUẤN LUYỆN MÔ HÌNH NHÁI GIỌNG (RVC V2) TRÊN NVIDIA RTX 3060 Ti ===")
print("=================================================================")

# 1. Tạo filelist.txt
print("\n[*] Đang tạo filelist dữ liệu...")
names = (
    set([p.stem for p in gt_wavs_dir.glob("*.wav")])
    & set([p.stem for p in feature_dir.glob("*.npy")])
    & set([p.stem.replace(".wav", "") for p in f0_dir.glob("*.npy")])
    & set([p.stem.replace(".wav", "") for p in f0nsf_dir.glob("*.npy")])
)

opt = []
for name in sorted(names):
    line = f"{gt_wavs_dir}/{name}.wav|{feature_dir}/{name}.npy|{f0_dir}/{name}.wav.npy|{f0nsf_dir}/{name}.wav.npy|0"
    opt.append(line.replace("\\", "/"))

random.shuffle(opt)
filelist_path = exp_dir / "filelist.txt"
with open(filelist_path, "w", encoding="utf-8") as f:
    f.write("\n".join(opt))
print(f"    [✓] Đã tạo filelist với {len(opt)} mẫu âm thanh huấn luyện.")

# 2. Tạo config.json
config_src = RVC_ROOT / "configs" / "v2" / "48k.json"
config_dst = exp_dir / "config.json"
with open(config_src, "r", encoding="utf-8") as f:
    config_data = json.load(f)

with open(config_dst, "w", encoding="utf-8") as f:
    json.dump(config_data, f, indent=4, ensure_ascii=False)
print(f"    [✓] Đã thiết lập cấu hình config.json (48kHz, V2).")

# 3. Huấn luyện mạng nơ-ron
print("\n[*] Bắt đầu huấn luyện mạng nơ-ron (30 Epochs trên GPU RTX 3060 Ti)...")
env = os.environ.copy()
env["PYTHONPATH"] = str(RVC_ROOT.resolve())
env["CUDA_VISIBLE_DEVICES"] = "0"

cmd_train = [
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
subprocess.run(cmd_train, cwd=str(RVC_ROOT), env=env, check=True)
print("    [✓] Huấn luyện mạng nơ-ron hoàn tất!")

# 4. Huấn luyện Index
print("\n[*] Đang xây dựng Feature Index (Faiss)...")
cmd_index = [
    PYTHON_EXE, "train/train_index.py",
    exp_name, "v2", "assets/indices", "4", "auto"
]
subprocess.run(cmd_index, cwd=str(RVC_ROOT), env=env, check=True)
print("    [✓] Xây dựng Index hoàn tất!")

# 5. Xuất mô hình vào models/
models_dir = PROJECT_ROOT / "models"
models_dir.mkdir(parents=True, exist_ok=True)

# Tìm file pth trong assets/weights
pth_weights = list((RVC_ROOT / "assets" / "weights").glob(f"*{exp_name}*.pth"))
if pth_weights:
    shutil.copy2(pth_weights[0], models_dir / "my_voice.pth")
    print(f"\n🎉 [THÀNH CÔNG] Đã lưu mô hình giọng nói: {models_dir / 'my_voice.pth'}")

index_files = list(exp_dir.glob("added_*.index"))
if not index_files:
    index_files = list((RVC_ROOT / "assets" / "indices").glob(f"*{exp_name}*.index"))
if index_files:
    shutil.copy2(index_files[0], models_dir / "my_voice.index")
    print(f"🎉 [THÀNH CÔNG] Đã lưu Faiss Index: {models_dir / 'my_voice.index'}")

print("\n=================================================================")
print("[✓] HUẤN LUYỆN GIỌNG NÓI CỦA BẠN HOÀN TẤT 100%!")
print("=================================================================")
