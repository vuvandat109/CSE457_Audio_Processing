# -*- coding: utf-8 -*-

"""
generate_sentence_analysis.py

Vietnamese ASR Sentence Analysis V14 - MULTI MODEL

Ho tro:
- Whisper base
- PhoWhisper base
- Chay rieng tung model hoac ca hai

Input:
- dataset/asr_results.csv
- dataset/asr_results_phowhisper.csv

Output:
- dataset/sentence_analysis_whisper.json
- dataset/sentence_analysis_phowhisper.json

Tuong thich cu:
- dataset/sentence_analysis.json van duoc cap nhat bang ket qua Whisper
"""

import argparse
import json
import logging
import sys
import unicodedata
from pathlib import Path

import pandas as pd
from tqdm import tqdm


# =====================================================
# IMPORT BACKEND
# =====================================================

ROOT = Path(__file__).resolve().parent
DATASET_DIR = ROOT.parent / "dataset"

sys.path.insert(
    0,
    str(
        ROOT.parent /
        "web" /
        "backend"
    )
)

from audio_analyzer import (
    word_alignment,
    simple_error_check,
    analyze_sentence_phoneme,
    calculate_score
)


log = logging.getLogger(__name__)


REQUIRED_COLUMNS = {
    "audio",
    "ground_truth",
    "prediction"
}


# =====================================================
# MODEL CONFIG
# =====================================================

MODEL_CONFIG = {
    "whisper": {
        "display_name": "Whisper base",
        "input": DATASET_DIR / "asr_results.csv",
        "output": DATASET_DIR / "sentence_analysis_whisper.json",
    },
    "phowhisper": {
        "display_name": "PhoWhisper base",
        "input": DATASET_DIR / "asr_results_phowhisper.csv",
        "output": DATASET_DIR / "sentence_analysis_phowhisper.json",
    },
    "wav2vec2": {
        "display_name": "Wav2Vec2 Vietnamese",
        "input": DATASET_DIR / "asr_results_wav2vec2.csv",
        "output": DATASET_DIR / "sentence_analysis_wav2vec2.json",
    }
}

LEGACY_WHISPER_OUTPUT = DATASET_DIR / "sentence_analysis.json"


# =====================================================
# NORMALIZE
# =====================================================

def normalize(text):

    if text is None:
        return ""

    return unicodedata.normalize(
        "NFC",
        str(text)
    ).strip()


# =====================================================
# ANALYZE ONE ROW
# =====================================================

def analyze_row(row, model_key, model_name):

    audio = normalize(
        row.get("audio")
    )

    reference = normalize(
        row.get("ground_truth")
    )

    prediction = normalize(
        row.get("prediction")
    )

    result = {
        "audio": audio,
        "model": model_key,
        "model_name": model_name,
        "ground_truth": reference,
        "prediction": prediction,
        "analysis_failed": False
    }

    try:

        # =========================
        # ALIGNMENT ONLY ONE TIME
        # =========================

        alignment = word_alignment(
            reference,
            prediction
        )

        errors = simple_error_check(
            alignment
        )

        word_analysis = analyze_sentence_phoneme(
            alignment
        )

        score = calculate_score(
            reference,
            prediction
        )

        result.update({
            "wer": score["wer"],
            "cer": score["cer"],

            "status": (
                "Đúng"
                if len(errors) == 0
                else
                "Sai"
            ),

            "errors": errors,
            "alignment": alignment,
            "word_analysis": word_analysis
        })

    except Exception as e:

        log.exception(
            "Analysis failed [%s]: %s",
            model_name,
            audio
        )

        result.update({
            "analysis_failed": True,
            "analysis_error": str(e),
            "status": "Lỗi phân tích",
            "errors": [
                "analysis_failed"
            ],
            "alignment": [],
            "word_analysis": [],
            "wer": None,
            "cer": None
        })

    return result


# =====================================================
# PROCESS ONE MODEL
# =====================================================

def process_model(model_key, input_file, output_file):

    model_info = MODEL_CONFIG[model_key]
    model_name = model_info["display_name"]

    print()
    print("==========================================")
    print("MODEL:", model_name)
    print("Input :", input_file)
    print("Output:", output_file)
    print("==========================================")

    if not input_file.exists():
        raise FileNotFoundError(
            f"Khong tim thay file input: {input_file}"
        )

    df = pd.read_csv(
        input_file,
        encoding="utf-8-sig",
        dtype=str,
        keep_default_na=False
    )

    missing = (
        REQUIRED_COLUMNS
        -
        set(df.columns)
    )

    if missing:
        raise ValueError(
            f"{input_file.name} missing columns: {missing}"
        )

    print(
        "ASR samples:",
        len(df)
    )

    results = []

    for row in tqdm(
        df.to_dict("records"),
        total=len(df),
        desc=model_name
    ):
        results.append(
            analyze_row(
                row,
                model_key,
                model_name
            )
        )

    failed = sum(
        1
        for x in results
        if x["analysis_failed"]
    )

    output = {
        "model": model_key,
        "model_name": model_name,
        "total_audio": len(results),
        "analysis_failed": failed,
        "data": results
    }

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            output,
            f,
            ensure_ascii=False,
            indent=2
        )

    # Giữ tương thích hệ thống cũ:
    # Whisper vẫn cập nhật sentence_analysis.json
    if model_key == "whisper":

        with open(
            LEGACY_WHISPER_OUTPUT,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                output,
                f,
                ensure_ascii=False,
                indent=2
            )

    print("--------------------------")
    print("DONE:", model_name)
    print("Total :", len(results))
    print("Failed:", failed)
    print("Saved :", output_file)

    if model_key == "whisper":
        print(
            "Legacy:",
            LEGACY_WHISPER_OUTPUT
        )

    return {
        "model": model_key,
        "model_name": model_name,
        "total": len(results),
        "failed": failed,
        "output": str(output_file)
    }


# =====================================================
# MAIN
# =====================================================

def main():

    logging.basicConfig(
        level=logging.INFO
    )

    parser = argparse.ArgumentParser(
        description="Generate sentence analysis for Whisper/PhoWhisper"
    )

    parser.add_argument(
        "--model",
        choices=[
            "whisper",
            "phowhisper",
            "wav2vec2",
            "all"
        ],
        default="all",
        help=(
            "Model can phan tich. "
            "Mac dinh: all"
        )
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help=(
            "Chi dung khi chay 1 model. "
            "Neu bo trong se dung file mac dinh."
        )
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Chi dung khi chay 1 model. "
            "Neu bo trong se dung file mac dinh."
        )
    )

    args = parser.parse_args()

    summaries = []

    if args.model == "all":

        if args.input is not None or args.output is not None:
            raise ValueError(
                "--input/--output chi dung khi --model whisper, "
                "--model phowhisper hoac --model wav2vec2"
            )

        for model_key in [
            "whisper",
            "phowhisper",
            "wav2vec2"
        ]:

            config = MODEL_CONFIG[
                model_key
            ]

            summaries.append(
                process_model(
                    model_key,
                    config["input"],
                    config["output"]
                )
            )

    else:

        config = MODEL_CONFIG[
            args.model
        ]

        input_file = (
            args.input
            if args.input is not None
            else config["input"]
        )

        output_file = (
            args.output
            if args.output is not None
            else config["output"]
        )

        summaries.append(
            process_model(
                args.model,
                input_file,
                output_file
            )
        )

    print()
    print("==========================================")
    print("ALL DONE")
    print("==========================================")

    for item in summaries:
        print(
            item["model_name"],
            "| Total:",
            item["total"],
            "| Failed:",
            item["failed"],
            "|",
            item["output"]
        )

    print("==========================================")


if __name__ == "__main__":
    main()
