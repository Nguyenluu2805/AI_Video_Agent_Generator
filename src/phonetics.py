import re
import json
from pathlib import Path

def load_phonetic_dict():
    project_root = Path(__file__).resolve().parent.parent
    dict_file = project_root / "config" / "pronunciation_dict.json"
    if dict_file.exists():
        try:
            with open(dict_file, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading dict: {e}")
    return {}

def normalize_phonetics(text: str) -> str:
    """
    Substitutes English terms with acoustic-optimized Vietnamese phonetic equivalents
    so that Vietnamese Neural TTS pronounces English words naturally and clearly.
    """
    phonetic_dict = load_phonetic_dict()
    # Sort phrases by length descending so multi-word matches first
    sorted_keys = sorted(phonetic_dict.keys(), key=lambda k: len(k), reverse=True)
    for term in sorted_keys:
        phonetic = phonetic_dict[term]
        pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
        text = pattern.sub(phonetic, text)
    return text

if __name__ == "__main__":
    sample = "Chào các bạn, hôm nay chúng ta sẽ tìm hiểu về Product Backlog, User Story, GoRide, Trello, INVEST, DEEP, Single Source of Truth trong mô hình Scrum."
    print("Original:", sample)
    print("Phonetic:", normalize_phonetics(sample))
