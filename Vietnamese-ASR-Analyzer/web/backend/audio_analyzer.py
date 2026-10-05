# -*- coding: utf-8 -*-

"""
audio_analyzer.py
Vietnamese ASR Analyzer V13.1 (fixed)

Features:
- WER / CER
- Word alignment DP
- Merge word detection (2 or 3 words)
- Split word detection
- Vietnamese phoneme error analysis
"""

from typing import List, Dict, Any, Optional
import re
import unicodedata
from difflib import SequenceMatcher

import jiwer

from vietnamese_phoneme import analyze_word


# =====================================================
# CONFIG
# =====================================================

MERGE_THRESHOLD = 0.55
SPLIT_THRESHOLD = 0.65


# =====================================================
# NORMALIZE
# =====================================================

def normalize_word(word: Optional[str]) -> str:
    if word is None:
        return ""

    word = unicodedata.normalize("NFC", str(word))
    word = word.lower()
    word = re.sub(r"[^\w]", "", word, flags=re.UNICODE)

    return word


def normalize_sentence(text: Optional[str]) -> str:
    if not text:
        return ""

    result = []
    for word in text.split():
        word = normalize_word(word)
        if word:
            result.append(word)

    return " ".join(result)


# =====================================================
# WER / CER
# =====================================================

def calculate_score(reference: Optional[str], prediction: Optional[str]) -> Dict[str, float]:
    ref = normalize_sentence(reference)
    hyp = normalize_sentence(prediction)

    # jiwer requires a non-empty reference; guard against div-by-zero style errors
    if not ref and not hyp:
        return {"wer": 0.0, "cer": 0.0}

    if not ref:
        # nothing to compare against: everything predicted is "extra"
        return {"wer": 1.0, "cer": 1.0}

    return {
        "wer": round(jiwer.wer(ref, hyp), 4),
        "cer": round(jiwer.cer(ref, hyp), 4),
    }


# =====================================================
# SIMILARITY
# =====================================================

def remove_tone(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text.replace("đ", "d")


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, remove_tone(a), remove_tone(b)).ratio()


# =====================================================
# WORD ALIGNMENT DP
# =====================================================

def word_alignment(reference: Optional[str], prediction: Optional[str]) -> List[Dict[str, str]]:
    if reference is None:
        reference = ""
    if prediction is None:
        prediction = ""

    ref = [normalize_word(x) for x in reference.split() if normalize_word(x)]
    hyp = [normalize_word(x) for x in prediction.split() if normalize_word(x)]

    m = len(ref)
    n = len(hyp)

    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if ref[i - 1] == hyp[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + cost,
            )

    result = []
    i = m
    j = n

    while i > 0 or j > 0:
        if i > 0 and j > 0 and ref[i - 1] == hyp[j - 1]:
            result.append({
                "type": "equal",
                "reference": ref[i - 1],
                "prediction": hyp[j - 1],
            })
            i -= 1
            j -= 1

        elif i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + 1:
            result.append({
                "type": "substitution",
                "reference": ref[i - 1],
                "prediction": hyp[j - 1],
            })
            i -= 1
            j -= 1

        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            result.append({
                "type": "missing_word",
                "reference": ref[i - 1],
                "prediction": "",
            })
            i -= 1

        else:
            result.append({
                "type": "extra_word",
                "reference": "",
                "prediction": hyp[j - 1],
            })
            j -= 1

    result.reverse()

    return post_process_alignment(result)


# =====================================================
# POST PROCESS ALIGNMENT
# MERGE / SPLIT WORD
# =====================================================

def post_process_alignment(alignment: List[Dict[str, str]]) -> List[Dict[str, str]]:
    result = []
    i = 0

    while i < len(alignment):
        current = alignment[i]

        # =====================================
        # MERGE 3 WORDS
        # ví dụ: a b c -> abc
        # (checked before merge-2 so it isn't
        # shadowed by a partial 2-word match)
        # =====================================

        if (
            i + 2 < len(alignment)
            and alignment[i]["type"] == "missing_word"
            and alignment[i + 1]["type"] == "missing_word"
            and alignment[i + 2]["type"] == "substitution"
        ):
            merged_ref = (
                alignment[i]["reference"]
                + alignment[i + 1]["reference"]
                + alignment[i + 2]["reference"]
            )

            score = similarity(merged_ref, alignment[i + 2]["prediction"])

            if score >= MERGE_THRESHOLD:
                result.append({
                    "type": "merge_word",
                    "reference": (
                        alignment[i]["reference"]
                        + " " + alignment[i + 1]["reference"]
                        + " " + alignment[i + 2]["reference"]
                    ),
                    "prediction": alignment[i + 2]["prediction"],
                })
                i += 3
                continue

        # =====================================
        # MERGE 2 WORDS
        # ví dụ: là anh -> lãn
        # =====================================

        if (
            i + 1 < len(alignment)
            and current["type"] == "missing_word"
            and alignment[i + 1]["type"] == "substitution"
        ):
            next_item = alignment[i + 1]
            merged_ref = current["reference"] + next_item["reference"]

            score = similarity(merged_ref, next_item["prediction"])

            if score >= MERGE_THRESHOLD:
                result.append({
                    "type": "merge_word",
                    "reference": current["reference"] + " " + next_item["reference"],
                    "prediction": next_item["prediction"],
                })
                i += 2
                continue

        # =====================================
        # SPLIT WORD
        # ví dụ: abc -> a bc
        # =====================================

        if (
            i + 1 < len(alignment)
            and current["type"] == "substitution"
            and alignment[i + 1]["type"] == "extra_word"
        ):
            combined = current["prediction"] + alignment[i + 1]["prediction"]
            score = similarity(current["reference"], combined)

            if score >= SPLIT_THRESHOLD:
                result.append({
                    "type": "split_word",
                    "reference": current["reference"],
                    "prediction": current["prediction"] + " " + alignment[i + 1]["prediction"],
                })
                i += 2
                continue

        result.append(current)
        i += 1

    return result


# =====================================================
# UNIQUE LIST, KEEP ORDER
# =====================================================

def unique_order(items: List[str]) -> List[str]:
    result = []
    for item in items:
        if item not in result:
            result.append(item)
    return result


# =====================================================
# PHONEME ERROR ANALYSIS
# =====================================================

def detect_word_error(reference: str, prediction: str):
    try:
        detail = analyze_word(reference, prediction)
    except Exception:
        return ["unknown_error"], None

    errors = []

    try:
        if not detail["initial"]["correct"]:
            errors.append("initial_consonant_error")

        if not detail["nucleus"]["correct"]:
            errors.append("nucleus_error")

        if not detail["final"]["correct"]:
            errors.append("final_consonant_error")

        if not detail["tone"]["correct"]:
            errors.append("tone_error")

    except Exception:
        errors.append("unknown_error")

    return errors, detail


# =====================================================
# ERROR CLASSIFIER
# =====================================================

def simple_error_check(alignment: List[Dict[str, str]]) -> List[str]:
    errors = []

    for item in alignment:
        typ = item["type"]

        if typ in ["missing_word", "extra_word", "merge_word", "split_word"]:
            errors.append(typ)

        elif typ == "substitution":
            e, _ = detect_word_error(item["reference"], item["prediction"])
            errors.extend(e)

    return unique_order(errors)


# =====================================================
# SENTENCE PHONEME DETAIL
# =====================================================

def analyze_sentence_phoneme(alignment: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Takes an already-computed alignment (list of dicts from word_alignment)
    and returns per-item phoneme error detail.
    """
    output = []

    for item in alignment:
        typ = item.get("type", "")
        ref = item.get("reference", "")
        hyp = item.get("prediction", "")

        if typ == "substitution":
            errors, detail = detect_word_error(ref, hyp)
            output.append({
                "type": typ,
                "reference": ref,
                "prediction": hyp,
                "errors": errors,
                "detail": detail,
            })
        else:
            output.append({
                "type": typ,
                "reference": ref,
                "prediction": hyp,
                "errors": [typ],
                "detail": None,
            })

    return output


def analyze_text_pair_phoneme(reference: Optional[str], prediction: Optional[str]) -> List[Dict[str, Any]]:
    """
    Convenience wrapper: computes alignment from raw reference/prediction
    strings and returns phoneme detail. Kept separate from
    analyze_sentence_phoneme() to avoid ambiguous overloaded signatures.
    """
    alignment = word_alignment(reference, prediction)
    return analyze_sentence_phoneme(alignment)


# =====================================================
# COMPLETE ANALYSIS
# =====================================================

def analyze_result(audio: str, reference: Optional[str], prediction: Optional[str]) -> Dict[str, Any]:
    score = calculate_score(reference, prediction)

    # alignment computed only once, reused below
    alignment = word_alignment(reference, prediction)

    errors = simple_error_check(alignment)
    detail = analyze_sentence_phoneme(alignment)

    return {
        "audio": audio,
        "ground_truth": reference,
        "prediction": prediction,
        "wer": score["wer"],
        "cer": score["cer"],
        "status": "Đúng" if not errors else "Sai",
        "errors": errors,
        "word_analysis": detail,
        "alignment": alignment,
    }


def analyze_text_pair(reference: Optional[str], prediction: Optional[str]) -> Dict[str, Any]:
    return analyze_result("test.mp3", reference, prediction)


# =====================================================
# QUICK TEST
# =====================================================

if __name__ == "__main__":
    tests = [
        ("là anh đây chỉ thăm hỏi đôi lời", "lãn đây chỉ tham hội đôi lời"),
        ("mày mà chạy nữa", "mày mà chảy nữa"),
        ("xin chào", "xin chào"),
        (None, "xin chào"),
        ("xin chào", None),
        ("", ""),
    ]

    for ref, hyp in tests:
        print("=" * 60)
        print("REFERENCE:", ref)
        print("PREDICTION:", hyp)
        print()

        try:
            alignment = word_alignment(ref, hyp)
            print("ALIGNMENT:")
            print(alignment)
            print()

            print("ERROR:")
            print(simple_error_check(alignment))
            print()

            print("SCORE:")
            print(calculate_score(ref, hyp))

        except Exception as e:
            print("EXCEPTION:", e)