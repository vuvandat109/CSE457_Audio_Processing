# -*- coding: utf-8 -*-

"""
generate_error_statistics.py

Vietnamese ASR Error Statistics V17 - MULTI MODEL

Tao thong ke rieng cho:
- Whisper base
- PhoWhisper base

Output:
- dataset/error_statistics_whisper.json
- dataset/error_statistics_phowhisper.json

Tuong thich cu:
- dataset/error_statistics.json = thong ke Whisper
"""

import argparse
import json
from pathlib import Path
from collections import Counter

import pandas as pd
from jiwer import process_words

from text_normalizer import normalize_vietnamese_text


ROOT = Path(__file__).resolve().parent
DATASET_DIR = ROOT.parent / "dataset"

MODEL_CONFIG = {
    "whisper": {
        "name": "Whisper base",
        "analysis": DATASET_DIR / "sentence_analysis_whisper.json",
        "results": DATASET_DIR / "asr_results.csv",
        "output": DATASET_DIR / "error_statistics_whisper.json",
    },
    "phowhisper": {
        "name": "PhoWhisper base",
        "analysis": DATASET_DIR / "sentence_analysis_phowhisper.json",
        "results": DATASET_DIR / "asr_results_phowhisper.csv",
        "output": DATASET_DIR / "error_statistics_phowhisper.json",
    },
    "wav2vec2": {
        "name": "Wav2Vec2 Vietnamese",
        "analysis": DATASET_DIR / "sentence_analysis_wav2vec2.json",
        "results": DATASET_DIR / "asr_results_wav2vec2.csv",
        "output": DATASET_DIR / "error_statistics_wav2vec2.json",
    },
}

LEGACY_OUTPUT = DATASET_DIR / "error_statistics.json"


def convert(obj):
    if isinstance(obj, Counter):
        return dict(obj)

    if isinstance(obj, dict):
        return {
            k: convert(v)
            for k, v in obj.items()
        }

    return obj


def generate_for_model(model_key: str):

    config = MODEL_CONFIG[model_key]

    print()
    print("==========================================")
    print("MODEL:", config["name"])
    print("==========================================")

    with open(
        config["analysis"],
        "r",
        encoding="utf-8"
    ) as f:
        data = json.load(f)

    samples = data.get("data", [])

    df_asr = pd.read_csv(
        config["results"],
        encoding="utf-8-sig"
    )

    wer_series = pd.to_numeric(
        df_asr["wer"],
        errors="coerce"
    )

    cer_series = pd.to_numeric(
        df_asr["cer"],
        errors="coerce"
    )

    valid_wer = wer_series.dropna()
    valid_cer = cer_series.dropna()

    average_wer = (
        float(valid_wer.mean())
        if len(valid_wer) > 0
        else 0.0
    )

    average_cer = (
        float(valid_cer.mean())
        if len(valid_cer) > 0
        else 0.0
    )

    error_distribution = Counter()

    phoneme_detail = {
        "initial": {
            "type": Counter(),
            "confusion": Counter()
        },
        "nucleus": {
            "confusion": Counter()
        },
        "final": {
            "type": Counter(),
            "confusion": Counter()
        },
        "tone": {
            "confusion": Counter()
        }
    }

    # Vietnamese-specific errors
    for sample in samples:

        for err in sample.get("errors", []):

            if err == "equal":
                continue

            error_distribution[err] += 1

        for word in sample.get("word_analysis", []):

            detail = word.get("detail")

            if not detail:
                continue

            initial = detail.get("initial")

            if initial and not initial.get("correct", True):

                phoneme_detail["initial"]["type"]["substitution"] += 1

                key = (
                    str(initial.get("reference", ""))
                    + " -> "
                    + str(initial.get("prediction", ""))
                )

                phoneme_detail["initial"]["confusion"][key] += 1

            nucleus = detail.get("nucleus")

            if nucleus and not nucleus.get("correct", True):

                key = (
                    str(nucleus.get("reference", ""))
                    + " -> "
                    + str(nucleus.get("prediction", ""))
                )

                phoneme_detail["nucleus"]["confusion"][key] += 1

            final = detail.get("final")

            if final and not final.get("correct", True):

                phoneme_detail["final"]["type"]["substitution"] += 1

                key = (
                    str(final.get("reference", ""))
                    + " -> "
                    + str(final.get("prediction", ""))
                )

                phoneme_detail["final"]["confusion"][key] += 1

            tone = detail.get("tone")

            if tone and not tone.get("correct", True):

                key = (
                    str(tone.get("reference", ""))
                    + " -> "
                    + str(tone.get("prediction", ""))
                )

                phoneme_detail["tone"]["confusion"][key] += 1

    total_substitutions = 0
    total_deletions = 0
    total_insertions = 0
    total_hits = 0

    hallucination_samples = []
    worst_audio = []

    for _, row in df_asr.iterrows():

        audio_name = str(row.get("audio", "")).strip()
        ground_truth = str(row.get("ground_truth", "")).strip()
        prediction = str(row.get("prediction", "")).strip()

        current_wer = pd.to_numeric(
            pd.Series([row.get("wer")]),
            errors="coerce"
        ).iloc[0]

        current_cer = pd.to_numeric(
            pd.Series([row.get("cer")]),
            errors="coerce"
        ).iloc[0]

        gt_norm = normalize_vietnamese_text(
            ground_truth
        )

        pred_norm = normalize_vietnamese_text(
            prediction
        )

        if gt_norm:

            try:

                measures = process_words(
                    gt_norm,
                    pred_norm
                )

                total_substitutions += int(
                    measures.substitutions
                )

                total_deletions += int(
                    measures.deletions
                )

                total_insertions += int(
                    measures.insertions
                )

                total_hits += int(
                    measures.hits
                )

            except Exception:
                pass

        ref_words = len(gt_norm.split())
        pred_words = len(pred_norm.split())

        word_ratio = (
            pred_words / ref_words
            if ref_words > 0
            else 0.0
        )

        severe_hallucination = False

        if pd.notna(current_wer):

            if float(current_wer) > 1.0:
                severe_hallucination = True

        if (
            ref_words > 0
            and word_ratio >= 3.0
            and (pred_words - ref_words) >= 5
        ):
            severe_hallucination = True

        if severe_hallucination:

            hallucination_samples.append({
                "audio": audio_name,
                "ground_truth": ground_truth,
                "prediction": prediction,
                "wer": (
                    float(current_wer)
                    if pd.notna(current_wer)
                    else None
                ),
                "cer": (
                    float(current_cer)
                    if pd.notna(current_cer)
                    else None
                )
            })

        if pd.notna(current_wer):

            worst_audio.append({
                "audio": audio_name,
                "wer": float(current_wer),
                "cer": (
                    float(current_cer)
                    if pd.notna(current_cer)
                    else None
                ),
                "ground_truth": ground_truth,
                "prediction": prediction
            })

    # Dong bo missing/extra voi D/I
    error_distribution["missing_word"] = total_deletions
    error_distribution["extra_word"] = total_insertions

    total_error = sum(
        error_distribution.values()
    )

    reference_word_total = (
        total_hits
        + total_substitutions
        + total_deletions
    )

    corpus_wer = (
        (
            total_substitutions
            + total_deletions
            + total_insertions
        )
        / reference_word_total
        if reference_word_total > 0
        else 0.0
    )

    hallucination_samples.sort(
        key=lambda x: (
            x["wer"]
            if x["wer"] is not None
            else -1
        ),
        reverse=True
    )

    worst_audio.sort(
        key=lambda x: x["wer"],
        reverse=True
    )

    correct_sentence = sum(
        1
        for x in samples
        if x.get("status") in (
            "Đúng",
            "correct"
        )
    )

    incorrect_sentence = sum(
        1
        for x in samples
        if x.get("status") in (
            "Sai",
            "incorrect"
        )
    )

    failed_sentence = sum(
        1
        for x in samples
        if x.get("status") in (
            "Lỗi phân tích",
            "failed"
        )
    )

    output = {
        "model": model_key,
        "model_name": config["name"],

        "total_audio": len(samples),
        "total_error": total_error,

        "average_wer": average_wer,
        "average_cer": average_cer,

        "average_wer_percent": average_wer * 100,
        "average_cer_percent": average_cer * 100,

        "valid_wer_samples": int(len(valid_wer)),
        "valid_cer_samples": int(len(valid_cer)),

        "correct_sentence": correct_sentence,
        "incorrect_sentence": incorrect_sentence,
        "failed_sentence": failed_sentence,

        "word_error_counts": {
            "substitutions": total_substitutions,
            "deletions": total_deletions,
            "insertions": total_insertions,
            "hits": total_hits,
            "reference_words": reference_word_total
        },

        "corpus_wer": corpus_wer,
        "corpus_wer_percent": corpus_wer * 100,

        "hallucination": {
            "count": len(hallucination_samples),
            "samples": hallucination_samples[:50]
        },

        "error_distribution": convert(
            error_distribution
        ),

        "phoneme_detail": convert(
            phoneme_detail
        ),

        "worst_audio": worst_audio[:20]
    }

    with open(
        config["output"],
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            output,
            f,
            ensure_ascii=False,
            indent=2
        )

    # He thong cu van dung Whisper
    if model_key == "whisper":

        with open(
            LEGACY_OUTPUT,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                output,
                f,
                ensure_ascii=False,
                indent=2
            )

    print("Total audio:", len(samples))
    print("Total error:", total_error)
    print(
        "WER trung binh:",
        f"{average_wer * 100:.2f}%"
    )
    print(
        "CER trung binh:",
        f"{average_cer * 100:.2f}%"
    )
    print(
        "Corpus WER:",
        f"{corpus_wer * 100:.2f}%"
    )
    print(
        "S / D / I:",
        total_substitutions,
        "/",
        total_deletions,
        "/",
        total_insertions
    )
    print(
        "Hallucination:",
        len(hallucination_samples)
    )
    print("Saved:", config["output"])

    return output


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--model",
        choices=[
            "whisper",
            "phowhisper",
            "wav2vec2",
            "all"
        ],
        default="all"
    )

    args = parser.parse_args()

    if args.model == "all":

        generate_for_model("whisper")
        generate_for_model("phowhisper")
        generate_for_model("wav2vec2")

    else:

        generate_for_model(
            args.model
        )

    print()
    print("==========================================")
    print("ALL DONE")
    print("==========================================")


if __name__ == "__main__":
    main()
