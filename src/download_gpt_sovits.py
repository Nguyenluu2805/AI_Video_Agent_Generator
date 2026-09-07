import os
import sys
import urllib.request
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
    if output_path.exists() and output_path.stat().st_size > 1024 * 5:
        print(f"Already exists: {output_path.name} ({round(output_path.stat().st_size / (1024*1024), 2)} MB)")
        return
    print(f"Downloading {output_path.name}...")
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    urllib.request.install_opener(opener)
    with DownloadProgressBar(unit='B', unit_scale=True, miniters=1, desc=output_path.name) as t:
        urllib.request.urlretrieve(url, filename=str(output_path), reporthook=t.update_to)
    print(f"Saved: {output_path.name}")

def main():
    base_dir = Path("gpt_sovits_engine/GPT_SoVITS/pretrained_models")
    base_dir.mkdir(parents=True, exist_ok=True)
    
    files = [
        # HuBERT
        ("https://huggingface.co/lj1995/GPT-SoVITS/resolve/main/chinese-hubert-base/config.json", base_dir / "chinese-hubert-base" / "config.json"),
        ("https://huggingface.co/lj1995/GPT-SoVITS/resolve/main/chinese-hubert-base/preprocessor_config.json", base_dir / "chinese-hubert-base" / "preprocessor_config.json"),
        ("https://huggingface.co/lj1995/GPT-SoVITS/resolve/main/chinese-hubert-base/pytorch_model.bin", base_dir / "chinese-hubert-base" / "pytorch_model.bin"),
        
        # RoBERTa
        ("https://huggingface.co/lj1995/GPT-SoVITS/resolve/main/chinese-roberta-wwm-ext-large/config.json", base_dir / "chinese-roberta-wwm-ext-large" / "config.json"),
        ("https://huggingface.co/lj1995/GPT-SoVITS/resolve/main/chinese-roberta-wwm-ext-large/pytorch_model.bin", base_dir / "chinese-roberta-wwm-ext-large" / "pytorch_model.bin"),
        ("https://huggingface.co/lj1995/GPT-SoVITS/resolve/main/chinese-roberta-wwm-ext-large/tokenizer.json", base_dir / "chinese-roberta-wwm-ext-large" / "tokenizer.json"),
        
        # GSV v2 Final Pretrained
        ("https://huggingface.co/lj1995/GPT-SoVITS/resolve/main/gsv-v2final-pretrained/s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt", base_dir / "gsv-v2final-pretrained" / "s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt"),
        ("https://huggingface.co/lj1995/GPT-SoVITS/resolve/main/gsv-v2final-pretrained/s2G2333k.pth", base_dir / "gsv-v2final-pretrained" / "s2G2333k.pth"),
        ("https://huggingface.co/lj1995/GPT-SoVITS/resolve/main/gsv-v2final-pretrained/s2D2333k.pth", base_dir / "gsv-v2final-pretrained" / "s2D2333k.pth"),
    ]
    
    for url, path in files:
        download_url(url, path)
    print("\nAll GPT-SoVITS pretrained weights downloaded successfully!")

if __name__ == "__main__":
    main()
