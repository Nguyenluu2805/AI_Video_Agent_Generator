import urllib.request
import os
import sys
from pathlib import Path
from tqdm import tqdm

class DownloadProgressBar(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)

def download_url(url, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists() and output_path.stat().st_size > 1024 * 10:
        print(f"Already downloaded: {output_path.name} ({round(output_path.stat().st_size / (1024*1024), 2)} MB)")
        return
    print(f"Downloading {url} -> {output_path.name}...")
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    urllib.request.install_opener(opener)
    with DownloadProgressBar(unit='B', unit_scale=True, miniters=1, desc=output_path.name) as t:
        urllib.request.urlretrieve(url, filename=str(output_path), reporthook=t.update_to)
    print(f"Saved: {output_path.name} ({round(output_path.stat().st_size / (1024*1024), 2)} MB)")

def download_all_f5_assets():
    f5_dir = Path("models/f5_tts")
    f5_dir.mkdir(parents=True, exist_ok=True)
    
    files = [
        ("https://huggingface.co/SWivid/F5-TTS/resolve/main/F5TTS_v1_Base/model_1250000.safetensors", f5_dir / "model_1250000.safetensors"),
        ("https://huggingface.co/SWivid/F5-TTS/resolve/main/F5TTS_v1_Base/vocab.txt", f5_dir / "vocab.txt"),
        ("https://huggingface.co/charactr/vocos-mel-24khz/resolve/main/config.yaml", f5_dir / "vocos" / "config.yaml"),
        ("https://huggingface.co/charactr/vocos-mel-24khz/resolve/main/pytorch_model.bin", f5_dir / "vocos" / "pytorch_model.bin"),
    ]
    
    for url, out in files:
        download_url(url, out)
    print("All F5-TTS assets downloaded successfully!")

if __name__ == "__main__":
    download_all_f5_assets()
