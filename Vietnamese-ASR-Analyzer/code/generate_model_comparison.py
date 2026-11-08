# -*- coding: utf-8 -*-

"""
generate_model_comparison.py

So sanh 3 model ASR tren cung bo 1000 mau:
1. Whisper base
2. PhoWhisper base
3. Wav2Vec2 Vietnamese

Input:
- dataset/asr_results.csv
- dataset/asr_results_phowhisper.csv
- dataset/asr_results_wav2vec2.csv

Output:
- dataset/model_comparison.json
"""

import json
import re
import unicodedata
from pathlib import Path

import pandas as pd
from jiwer import process_words


ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = ROOT / "dataset"

MODELS = {
    "whisper_base": {
        "name": "Whisper base",
        "file": DATASET_DIR / "asr_results.csv",
    },
    "phowhisper_base": {
        "name": "PhoWhisper base",
        "file": DATASET_DIR / "asr_results_phowhisper.csv",
    },
    "wav2vec2_vietnamese": {
        "name": "Wav2Vec2 Vietnamese",
        "file": DATASET_DIR / "asr_results_wav2vec2.csv",
    },
}

OUTPUT_FILE = DATASET_DIR / "model_comparison.json"


def normalize_text(text):
    if text is None:
        return ""
    text = str(text)
    text = unicodedata.normalize("NFC", text)
    text = text.lower().strip()
    text = re.sub(r"[^\w\sÀ-ỹĐđ]", " ", text, flags=re.UNICODE)
    text = re.sub(r"_", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def find_col(df, names):
    mapping = {str(c).lower(): c for c in df.columns}
    for name in names:
        if name.lower() in mapping:
            return mapping[name.lower()]
    return None


def analyze_model(model_key, model_info):
    path = model_info["file"]

    if not path.exists():
        raise FileNotFoundError(f"Khong tim thay: {path}")

    df = pd.read_csv(path, encoding="utf-8-sig")

    audio_col = find_col(df, ["audio", "audio_file", "filename", "file"])
    gt_col = find_col(
        df,
        ["ground_truth", "reference", "sentence", "transcript", "text"]
    )
    pred_col = find_col(
        df,
        ["prediction", "hypothesis", "asr_text", "predicted_text"]
    )

    if gt_col is None or pred_col is None:
        raise ValueError(
            f"{path.name}: khong tim thay cot ground_truth/prediction. "
            f"Cac cot: {list(df.columns)}"
        )

    wer_values = pd.to_numeric(df["wer"], errors="coerce")
    cer_values = pd.to_numeric(df["cer"], errors="coerce")

    valid_wer = wer_values.dropna()
    valid_cer = cer_values.dropna()

    substitutions = 0
    deletions = 0
    insertions = 0
    hits = 0

    hallucination_count = 0
    hallucination_samples = []

    for idx, row in df.iterrows():
        gt_raw = row.get(gt_col, "")
        pred_raw = row.get(pred_col, "")

        gt = normalize_text(gt_raw)
        pred = normalize_text(pred_raw)

        if gt:
            try:
                measures = process_words(gt, pred)
                substitutions += int(measures.substitutions)
                deletions += int(measures.deletions)
                insertions += int(measures.insertions)
                hits += int(measures.hits)
            except Exception:
                pass

        current_wer = pd.to_numeric(
            pd.Series([row.get("wer")]),
            errors="coerce"
        ).iloc[0]

        ref_words = len(gt.split())
        pred_words = len(pred.split())

        ratio = (
            pred_words / ref_words
            if ref_words > 0
            else 0.0
        )

        suspected_hallucination = False

        if pd.notna(current_wer) and float(current_wer) > 1.0:
            suspected_hallucination = True

        if (
            ref_words > 0
            and ratio >= 3.0
            and pred_words - ref_words >= 5
        ):
            suspected_hallucination = True

        if suspected_hallucination:
            hallucination_count += 1

            if len(hallucination_samples) < 20:
                hallucination_samples.append({
                    "audio": (
                        str(row.get(audio_col, ""))
                        if audio_col is not None
                        else str(idx)
                    ),
                    "ground_truth": str(gt_raw),
                    "prediction": str(pred_raw),
                    "wer": (
                        float(current_wer)
                        if pd.notna(current_wer)
                        else None
                    )
                })

    reference_words = hits + substitutions + deletions

    corpus_wer = (
        (substitutions + deletions + insertions) / reference_words
        if reference_words > 0
        else 0.0
    )

    return {
        "key": model_key,
        "name": model_info["name"],
        "file": path.name,
        "total_audio": int(len(df)),
        "valid_wer_samples": int(len(valid_wer)),
        "valid_cer_samples": int(len(valid_cer)),
        "average_wer": float(valid_wer.mean()) if len(valid_wer) else 0.0,
        "average_cer": float(valid_cer.mean()) if len(valid_cer) else 0.0,
        "corpus_wer": float(corpus_wer),
        "substitutions": int(substitutions),
        "deletions": int(deletions),
        "insertions": int(insertions),
        "hits": int(hits),
        "reference_words": int(reference_words),
        "hallucination_count": int(hallucination_count),
        "hallucination_samples": hallucination_samples,
    }


print("Generating model comparison...")

models = []

for key, info in MODELS.items():
    print("Analyzing:", info["name"])
    models.append(analyze_model(key, info))


best_wer = min(models, key=lambda x: x["average_wer"])
best_cer = min(models, key=lambda x: x["average_cer"])
best_corpus_wer = min(models, key=lambda x: x["corpus_wer"])
best_hallucination = min(models, key=lambda x: x["hallucination_count"])

output = {
    "models": models,
    "best": {
        "average_wer": best_wer["key"],
        "average_cer": best_cer["key"],
        "corpus_wer": best_corpus_wer["key"],
        "hallucination_count": best_hallucination["key"],
    }
}

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        output,
        f,
        ensure_ascii=False,
        indent=2
    )

print()
print("==============================================")
print("MODEL COMPARISON")
print("==============================================")

for model in models:
    print(model["name"])
    print("  WER trung binh:", f'{model["average_wer"] * 100:.2f}%')
    print("  CER trung binh:", f'{model["average_cer"] * 100:.2f}%')
    print("  Corpus WER:", f'{model["corpus_wer"] * 100:.2f}%')
    print(
        "  S / D / I:",
        model["substitutions"],
        "/",
        model["deletions"],
        "/",
        model["insertions"]
    )
    print("  Hallucination:", model["hallucination_count"])
    print("----------------------------------------------")

print("Best average WER:", best_wer["name"])
print("Best average CER:", best_cer["name"])
print("Best corpus WER:", best_corpus_wer["name"])
print("Saved:", OUTPUT_FILE)
print("==============================================")
