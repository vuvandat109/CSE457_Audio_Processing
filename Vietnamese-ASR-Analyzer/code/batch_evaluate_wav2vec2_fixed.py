# -*- coding: utf-8 -*-

"""
batch_evaluate_wav2vec2.py
FIX V2

Model 3:
khanhld/wav2vec2-base-vietnamese-160h

Sua 2 van de:
1. Khong dung torchaudio.load cho MP3 -> dung librosa.load
2. Ep Transformers dung pytorch_model.bin -> use_safetensors=False
   de tranh luong auto-conversion goi Hugging Face Discussions bi 403.

Mac dinh test 20 mau.
"""

from pathlib import Path
import re
import unicodedata

import librosa
import numpy as np
import pandas as pd
import torch
from jiwer import wer, cer
from transformers import AutoProcessor, AutoModelForCTC
from tqdm import tqdm


# =====================================================
# CONFIG
# =====================================================

ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = ROOT / "dataset"

METADATA_FILE = DATASET_DIR / "metadata.csv"
AUDIO_DIR = DATASET_DIR / "audio"

MODEL_ID = "khanhld/wav2vec2-base-vietnamese-160h"

TEST_LIMIT = 20

OUTPUT_FILE = DATASET_DIR / "asr_results_wav2vec2_test.csv"

TARGET_SAMPLE_RATE = 16000


# =====================================================
# NORMALIZE TEXT
# =====================================================

def normalize_text(text):

    if text is None:
        return ""

    text = str(text)
    text = unicodedata.normalize("NFC", text)
    text = text.lower().strip()

    text = re.sub(
        r"[^\w\sÀ-ỹĐđ]",
        " ",
        text,
        flags=re.UNICODE
    )

    text = re.sub(r"_", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


# =====================================================
# FIND COLUMN
# =====================================================

def find_column(df, candidates):

    lower_map = {
        str(c).lower(): c
        for c in df.columns
    }

    for candidate in candidates:

        if candidate.lower() in lower_map:
            return lower_map[candidate.lower()]

    return None


# =====================================================
# LOAD AUDIO
# =====================================================

def load_audio(path: Path):

    # librosa doc MP3 va tu resample ve 16 kHz
    waveform, _ = librosa.load(
        str(path),
        sr=TARGET_SAMPLE_RATE,
        mono=True
    )

    waveform = np.asarray(
        waveform,
        dtype=np.float32
    )

    return waveform


# =====================================================
# LOAD METADATA
# =====================================================

print("Loading metadata...")

df = pd.read_csv(
    METADATA_FILE,
    encoding="utf-8-sig"
)

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
        "Khong tim thay cot audio. "
        f"Cac cot hien co: {list(df.columns)}"
    )

if text_col is None:
    raise ValueError(
        "Khong tim thay cot ground truth. "
        f"Cac cot hien co: {list(df.columns)}"
    )

if TEST_LIMIT is not None:
    df = df.head(TEST_LIMIT).copy()

print("Audio column:", audio_col)
print("Text column :", text_col)
print("Samples     :", len(df))


# =====================================================
# LOAD MODEL
# =====================================================

device = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else
    "cpu"
)

print()
print("==============================")
print("Loading Wav2Vec2...")
print("Model :", MODEL_ID)
print("Device:", device)
print("==============================")


processor = AutoProcessor.from_pretrained(
    MODEL_ID
)

model = AutoModelForCTC.from_pretrained(
    MODEL_ID,
    use_safetensors=False
)

model.to(device)
model.eval()


# =====================================================
# EVALUATE
# =====================================================

results = []

for _, row in tqdm(
    df.iterrows(),
    total=len(df),
    desc="Wav2Vec2"
):

    audio_name = str(
        row[audio_col]
    ).strip()

    ground_truth_raw = str(
        row[text_col]
    ).strip()

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

        print()
        print("[ERROR]", audio_name, "Audio file not found")
        continue

    gt = normalize_text(
        ground_truth_raw
    )

    try:

        waveform = load_audio(
            audio_path
        )

        inputs = processor(
            waveform,
            sampling_rate=TARGET_SAMPLE_RATE,
            return_tensors="pt",
            padding=True
        )

        input_values = inputs.input_values.to(
            device
        )

        attention_mask = getattr(
            inputs,
            "attention_mask",
            None
        )

        if attention_mask is not None:
            attention_mask = attention_mask.to(
                device
            )

        with torch.inference_mode():

            outputs = model(
                input_values,
                attention_mask=attention_mask
            )

        predicted_ids = torch.argmax(
            outputs.logits,
            dim=-1
        )

        prediction_raw = processor.batch_decode(
            predicted_ids
        )[0]

        pred = normalize_text(
            prediction_raw
        )

        if gt:

            sample_wer = float(
                wer(gt, pred)
            )

            sample_cer = float(
                cer(gt, pred)
            )

        else:

            sample_wer = (
                0.0
                if not pred
                else 1.0
            )

            sample_cer = (
                0.0
                if not pred
                else 1.0
            )

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
            "error": repr(exc)
        })

        print()
        print("--------------------------------")
        print("[ERROR]", audio_name)
        print(type(exc).__name__ + ":", exc)


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
print(
    "That bai:",
    len(result_df) - len(valid)
)

if len(valid) > 0:

    print(
        "WER trung binh:",
        float(valid["wer"].mean())
    )

    print(
        "CER trung binh:",
        float(valid["cer"].mean())
    )

else:

    print()
    print("Khong co mau nao chay thanh cong.")
    print("Hay xem cac dong [ERROR] phia tren.")
    print("Cot error cung da duoc luu trong CSV.")

print("Da luu ket qua tai:")
print(OUTPUT_FILE)
print("==============================")
