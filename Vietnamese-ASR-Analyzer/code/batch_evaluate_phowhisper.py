# -*- coding: utf-8 -*-

"""
batch_evaluate_phowhisper.py

Danh gia model 2: vinai/PhoWhisper-base
- Doc metadata.csv
- Nhan dang audio trong dataset/audio
- Tinh WER/CER
- Mac dinh test 20 mau truoc
- Khong ghi de ket qua Whisper

Output test:
dataset/asr_results_phowhisper_test.csv

Khi test on, doi TEST_LIMIT = 1000 va OUTPUT_FILE thanh
dataset/asr_results_phowhisper.csv
"""

from pathlib import Path
import re
import unicodedata

import pandas as pd
import torch
from jiwer import wer, cer
from transformers import pipeline
from tqdm import tqdm


# =====================================================
# CONFIG
# =====================================================

ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = ROOT / "dataset"

METADATA_FILE = DATASET_DIR / "metadata.csv"
AUDIO_DIR = DATASET_DIR / "audio"

MODEL_ID = "vinai/PhoWhisper-base"

TEST_LIMIT = 20

OUTPUT_FILE = DATASET_DIR / "asr_results_phowhisper_test.csv"


# =====================================================
# TEXT NORMALIZATION
# =====================================================

def normalize_text(text):
    if text is None:
        return ""

    text = str(text)
    text = unicodedata.normalize("NFC", text)
    text = text.lower().strip()

    # Bo dau cau, giu chu cai/so/Unicode tieng Viet
    text = re.sub(r"[^\w\sÀ-ỹĐđ]", " ", text, flags=re.UNICODE)
    text = re.sub(r"_", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


# =====================================================
# FIND COLUMNS
# =====================================================

def find_column(df, candidates):
    lower_map = {str(c).lower(): c for c in df.columns}

    for candidate in candidates:
        if candidate.lower() in lower_map:
            return lower_map[candidate.lower()]

    return None


# =====================================================
# LOAD METADATA
# =====================================================

print("Loading metadata...")

df = pd.read_csv(METADATA_FILE, encoding="utf-8-sig")

audio_col = find_column(
    df,
    [
        "audio",
        "audio_file",
        "audio_path",
        "path",
        "filename",
        "file",
        "wav",
        "mp3"
    ]
)

text_col = find_column(
    df,
    [
        "ground_truth",
        "sentence",
        "transcript",
        "text",
        "reference",
        "normalized_text"
    ]
)

if audio_col is None:
    raise ValueError(
        "Khong tim thay cot ten audio trong metadata.csv. "
        f"Cac cot hien co: {list(df.columns)}"
    )

if text_col is None:
    raise ValueError(
        "Khong tim thay cot cau chuan trong metadata.csv. "
        f"Cac cot hien co: {list(df.columns)}"
    )

if TEST_LIMIT is not None:
    df = df.head(TEST_LIMIT).copy()

print("Audio column:", audio_col)
print("Text column:", text_col)
print("Samples:", len(df))


# =====================================================
# LOAD MODEL
# =====================================================

device = 0 if torch.cuda.is_available() else -1

print("==============================")
print("Loading PhoWhisper...")
print("Model:", MODEL_ID)
print(
    "Device:",
    "CUDA" if device == 0 else "CPU"
)
print("==============================")

asr = pipeline(
    task="automatic-speech-recognition",
    model=MODEL_ID,
    device=device
)


# =====================================================
# EVALUATE
# =====================================================

results = []

for idx, row in tqdm(
    df.iterrows(),
    total=len(df),
    desc="PhoWhisper"
):
    audio_name = str(row[audio_col]).strip()
    ground_truth_raw = str(row[text_col]).strip()

    # metadata co the chua duong dan con hoac chi ten file
    candidate = Path(audio_name)

    if candidate.is_absolute():
        audio_path = candidate
    else:
        audio_path = AUDIO_DIR / candidate.name

    if not audio_path.exists():
        results.append({
            "audio": audio_name,
            "ground_truth": ground_truth_raw,
            "prediction": "",
            "wer": None,
            "cer": None,
            "status": "failed",
            "error": "Audio file not found"
        })
        continue

    gt = normalize_text(ground_truth_raw)

    try:
        output = asr(
            str(audio_path),
            generate_kwargs={
                "language": "vi",
                "task": "transcribe"
            }
        )

        prediction_raw = (
            output.get("text", "")
            if isinstance(output, dict)
            else str(output)
        )

        pred = normalize_text(prediction_raw)

        if gt:
            sample_wer = float(wer(gt, pred))
            sample_cer = float(cer(gt, pred))
        else:
            sample_wer = 0.0 if not pred else 1.0
            sample_cer = 0.0 if not pred else 1.0

        results.append({
            "audio": audio_name,
            "ground_truth": ground_truth_raw,
            "prediction": prediction_raw.strip(),
            "wer": sample_wer,
            "cer": sample_cer,
            "status": "ok",
            "error": ""
        })

        print()
        print("--------------------------------")
        print("Audio:", audio_name)
        print("GT :", gt)
        print("ASR:", pred)
        print("WER:", sample_wer)
        print("CER:", sample_cer)

    except Exception as exc:
        results.append({
            "audio": audio_name,
            "ground_truth": ground_truth_raw,
            "prediction": "",
            "wer": None,
            "cer": None,
            "status": "failed",
            "error": str(exc)
        })

        print()
        print("[ERROR]", audio_name, exc)


# =====================================================
# SAVE
# =====================================================

result_df = pd.DataFrame(results)

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

result_df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

valid = result_df[
    result_df["wer"].notna()
].copy()

print()
print("==============================")
print("MODEL:", MODEL_ID)
print("Tong mau:", len(result_df))
print("Thanh cong:", len(valid))
print("That bai:", len(result_df) - len(valid))

if len(valid) > 0:
    print(
        "WER trung binh:",
        float(valid["wer"].mean())
    )
    print(
        "CER trung binh:",
        float(valid["cer"].mean())
    )

print("Da luu ket qua tai:")
print(OUTPUT_FILE)
print("==============================")
