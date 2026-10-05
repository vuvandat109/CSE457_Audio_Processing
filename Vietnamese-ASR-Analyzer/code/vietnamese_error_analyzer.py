from vietnamese_phonology import parse_syllable
from vietnamese_validator import (
    is_valid_vietnamese_token,
    classify_token
)


def compare_components(reference, hypothesis):
    """
    So sánh các thành phần âm tiết của từ đúng
    và từ mà ASR nhận dạng.
    """

    ref = parse_syllable(reference)
    hyp = parse_syllable(hypothesis)

    return {
        "reference": ref,
        "hypothesis": hyp,

        "initial_changed":
            ref["initial"] != hyp["initial"],

        "medial_changed":
            ref["medial"] != hyp["medial"],

        "nucleus_changed":
            ref["nucleus"] != hyp["nucleus"],

        "coda_changed":
            ref["coda"] != hyp["coda"],

        "tone_changed":
            ref["tone"] != hyp["tone"]
    }


def analyze_word_error(reference, hypothesis):
    """
    Phân tích một cặp từ:

        reference:
            từ đúng trong Ground Truth

        hypothesis:
            từ mà hệ thống ASR nhận dạng

    Ví dụ:

        chạy -> chảy
            tone_error

        trời -> chời
            initial_consonant_error

        nước -> nức
            nucleus_error

        rừng -> vungınız
            non_vietnamese_token
    """

    # ======================================================
    # 1. KIỂM TRA TOKEN
    # ======================================================

    ref_valid = is_valid_vietnamese_token(
        reference
    )

    hyp_valid = is_valid_vietnamese_token(
        hypothesis
    )

    # ------------------------------------------------------
    # Ground Truth không hợp lệ
    # ------------------------------------------------------

    if not ref_valid:

        ref_check = classify_token(
            reference
        )

        return {
            "error_type": "invalid_reference_token",
            "changed_components": [],

            "reference_valid": False,
            "hypothesis_valid": hyp_valid,

            "reference_validation_reason":
                ref_check["reason"],

            "hypothesis_validation_reason":
                (
                    "valid"
                    if hyp_valid
                    else classify_token(
                        hypothesis
                    )["reason"]
                ),

            "reference": None,
            "hypothesis": None
        }

    # ------------------------------------------------------
    # ASR sinh token không hợp lệ
    # ------------------------------------------------------

    if not hyp_valid:

        hyp_check = classify_token(
            hypothesis
        )

        return {
            "error_type": "non_vietnamese_token",
            "changed_components": [],

            "reference_valid": True,
            "hypothesis_valid": False,

            "reference_validation_reason":
                "valid",

            "hypothesis_validation_reason":
                hyp_check["reason"],

            "reference":
                parse_syllable(reference),

            "hypothesis": None
        }

    # ======================================================
    # 2. CẢ HAI TOKEN HỢP LỆ
    # ======================================================

    comparison = compare_components(
        reference,
        hypothesis
    )

    ref = comparison["reference"]
    hyp = comparison["hypothesis"]

    # ======================================================
    # 3. KIỂM TRA TỪ GIỐNG NHAU
    # ======================================================

    if (
        ref["base"] == hyp["base"]
        and
        ref["tone"] == hyp["tone"]
    ):

        return {
            "error_type": "correct",
            "changed_components": [],

            "reference_valid": True,
            "hypothesis_valid": True,

            "reference_validation_reason":
                "valid",

            "hypothesis_validation_reason":
                "valid",

            **comparison
        }

    # ======================================================
    # 4. XÁC ĐỊNH THÀNH PHẦN BỊ SAI
    # ======================================================

    changed = []

    if comparison["initial_changed"]:
        changed.append(
            "initial"
        )

    if comparison["medial_changed"]:
        changed.append(
            "medial"
        )

    if comparison["nucleus_changed"]:
        changed.append(
            "nucleus"
        )

    if comparison["coda_changed"]:
        changed.append(
            "coda"
        )

    if comparison["tone_changed"]:
        changed.append(
            "tone"
        )

    # ======================================================
    # 5. PHÂN LOẠI LỖI
    # ======================================================

    if changed == ["tone"]:

        error_type = "tone_error"

    elif changed == ["initial"]:

        error_type = "initial_consonant_error"

    elif changed == ["medial"]:

        error_type = "medial_error"

    elif changed == ["nucleus"]:

        error_type = "nucleus_error"

    elif changed == ["coda"]:

        error_type = "final_consonant_error"

    elif len(changed) > 1:

        error_type = "multi_component_error"

    else:

        error_type = "unknown"

    # ======================================================
    # 6. TRẢ KẾT QUẢ
    # ======================================================

    return {
        "error_type": error_type,
        "changed_components": changed,

        "reference_valid": True,
        "hypothesis_valid": True,

        "reference_validation_reason":
            "valid",

        "hypothesis_validation_reason":
            "valid",

        **comparison
    }


# ==========================================================
# TEST NHANH
# ==========================================================

if __name__ == "__main__":

    test_pairs = [
        ("chạy", "chảy"),
        ("già", "giả"),
        ("lãnh", "lánh"),
        ("ánh", "anh"),

        ("trời", "chời"),
        ("sang", "xang"),

        ("ban", "bang"),
        ("lan", "lang"),

        ("hoa", "ha"),

        ("nước", "nức"),

        ("trời", "trời"),

        # Token ASR không hợp lệ
        ("rừng", "vungınız"),
        ("nước", "123"),
        ("trời", "xyz")
    ]

    print(
        "===== TEST VIETNAMESE ERROR ANALYZER ====="
    )

    for ref, hyp in test_pairs:

        result = analyze_word_error(
            ref,
            hyp
        )

        print(
            f"{ref:10} -> {hyp:12} "
            f": {result['error_type']}"
        )