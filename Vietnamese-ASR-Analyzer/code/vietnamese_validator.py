import re
import unicodedata

from vietnamese_phonology import parse_syllable


# ==========================================================
# 1. CAC KY TU NGUYEN AM TIENG VIET
# ==========================================================

VIETNAMESE_VOWELS = set(
    "aăâeêioôơuưy"
)


# ==========================================================
# 2. CAC PHU AM DAU DUOC CHAP NHAN
# ==========================================================

VALID_INITIALS = {
    "",
    "b",
    "c",
    "ch",
    "d",
    "đ",
    "g",
    "gh",
    "gi",
    "h",
    "k",
    "kh",
    "l",
    "m",
    "n",
    "ng",
    "ngh",
    "nh",
    "p",
    "ph",
    "q",
    "qu",
    "r",
    "s",
    "t",
    "th",
    "tr",
    "v",
    "x"
}


# ==========================================================
# 3. CAC AM CUOI DUOC CHAP NHAN
# ==========================================================

VALID_CODAS = {
    "",
    "c",
    "ch",
    "m",
    "n",
    "ng",
    "nh",
    "p",
    "t",
    "i",
    "y",
    "o",
    "u"
}


# ==========================================================
# 4. CAC AM CHINH / CUM NGUYEN AM THUONG GAP
# ==========================================================
#
# Day la lop kiem tra cau truc chinh ta.
# Muc dich:
# tranh cac token la nhu xyz, qza...
# bi dua vao bo phan tich loi tieng Viet.
#
# Day KHONG phai la tu dien tieng Viet day du.

VALID_NUCLEI = {
    # Nguyen am don
    "a",
    "ă",
    "â",
    "e",
    "ê",
    "i",
    "o",
    "ô",
    "ơ",
    "u",
    "ư",
    "y",

    # Cum nguyen am pho bien
    "ai",
    "ao",
    "au",
    "ay",
    "âu",
    "ây",

    "eo",
    "êu",

    "ia",
    "iê",
    "iu",

    "oa",
    "oă",
    "oe",
    "oi",
    "ôi",
    "ơi",

    "ua",
    "uâ",
    "uê",
    "ui",
    "ưi",

    "ưa",
    "ươ",
    "ưu",

    "ya",
    "yê",
    "yu"
}


# ==========================================================
# 5. CHUAN HOA TOKEN
# ==========================================================

def normalize_token(word):
    """
    Chuan hoa token truoc khi kiem tra.
    """

    if word is None:
        return ""

    word = str(word).strip().lower()

    word = unicodedata.normalize(
        "NFC",
        word
    )

    return word


# ==========================================================
# 6. KIEM TRA TOKEN CO CHUA SO KHONG
# ==========================================================

def contains_number(word):
    """
    Tra ve True neu token co chua chu so.
    """

    return any(
        char.isdigit()
        for char in word
    )


# ==========================================================
# 7. KIEM TRA KY TU KHONG THUOC HE CHU TIENG VIET
# ==========================================================

def contains_invalid_character(word):
    """
    Chi cho phep cac chu cai co the xuat hien
    trong van ban tieng Viet.
    """

    pattern = (
        r"^[a-z"
        r"àáảãạ"
        r"ăằắẳẵặ"
        r"âầấẩẫậ"
        r"èéẻẽẹ"
        r"êềếểễệ"
        r"ìíỉĩị"
        r"òóỏõọ"
        r"ôồốổỗộ"
        r"ơờớởỡợ"
        r"ùúủũụ"
        r"ưừứửữự"
        r"ỳýỷỹỵ"
        r"đ]+$"
    )

    return (
        re.fullmatch(
            pattern,
            word
        )
        is None
    )


# ==========================================================
# 8. KIEM TRA CO NGUYEN AM KHONG
# ==========================================================

def has_vowel(word):
    """
    Mot am tiet tieng Viet can co nguyen am.
    """

    word = normalize_token(word)

    # Bo dau thanh nhung van giu
    # a/ă/â, o/ô/ơ, u/ư...
    decomposed = unicodedata.normalize(
        "NFD",
        word
    )

    result = []

    for char in decomposed:

        # Bo cac dau ket hop
        if unicodedata.combining(char):
            continue

        result.append(char)

    base_word = unicodedata.normalize(
        "NFC",
        "".join(result)
    )

    return any(
        char in VIETNAMESE_VOWELS
        for char in base_word
    )


# ==========================================================
# 9. KIEM TRA CAC THANH PHAN DO PARSER TRA VE
# ==========================================================

def validate_parsed_parts(parts):
    """
    Kiem tra cau truc am tiet sau khi parser da tach.

    Tra ve:
        (True, "valid")

    hoac:
        (False, "ly_do")
    """

    initial = parts.get(
        "initial",
        ""
    )

    medial = parts.get(
        "medial",
        ""
    )

    nucleus = parts.get(
        "nucleus",
        ""
    )

    coda = parts.get(
        "coda",
        ""
    )

    # ------------------------------------------
    # Kiem tra phu am dau
    # ------------------------------------------

    if initial not in VALID_INITIALS:

        return (
            False,
            "invalid_initial"
        )

    # ------------------------------------------
    # Kiem tra am cuoi
    # ------------------------------------------

    if coda not in VALID_CODAS:

        return (
            False,
            "invalid_coda"
        )

    # ------------------------------------------
    # Phai co am chinh
    # ------------------------------------------

    if not nucleus:

        return (
            False,
            "no_nucleus"
        )

    # ------------------------------------------
    # Am chinh phai nam trong tap cho phep
    # ------------------------------------------

    if nucleus not in VALID_NUCLEI:

        return (
            False,
            "invalid_nucleus"
        )

    # ------------------------------------------
    # Am dem cua parser hien tai chi dung o/u
    # ------------------------------------------

    if medial not in {
        "",
        "o",
        "u"
    }:

        return (
            False,
            "invalid_medial"
        )

    return (
        True,
        "valid"
    )


# ==========================================================
# 10. KIEM TRA TOKEN TIENG VIET
# ==========================================================

def is_valid_vietnamese_token(word):
    """
    Kiem tra token co phu hop de dua vao
    bo phan tich am tiet tieng Viet hay khong.

    True:
        Co the dua vao phan tich.

    False:
        Khong nen dua vao phan tich.
    """

    result = classify_token(
        word
    )

    return result["valid"]


# ==========================================================
# 11. PHAN LOAI TOKEN VA TRA VE LY DO
# ==========================================================

def classify_token(word):
    """
    Kiem tra chi tiet mot token.

    Ket qua vi du:

    {
        "token": "nuoc",
        "valid": True,
        "reason": "valid"
    }

    Hoac:

    {
        "token": "123",
        "valid": False,
        "reason": "contains_number"
    }
    """

    word = normalize_token(
        word
    )

    # ------------------------------------------
    # Token rong
    # ------------------------------------------

    if not word:

        return {
            "token": word,
            "valid": False,
            "reason": "empty_token"
        }

    # ------------------------------------------
    # Co chu so
    # ------------------------------------------

    if contains_number(word):

        return {
            "token": word,
            "valid": False,
            "reason": "contains_number"
        }

    # ------------------------------------------
    # Co ky tu la
    # ------------------------------------------

    if contains_invalid_character(word):

        return {
            "token": word,
            "valid": False,
            "reason": "invalid_character"
        }

    # ------------------------------------------
    # Khong co nguyen am
    # ------------------------------------------

    if not has_vowel(word):

        return {
            "token": word,
            "valid": False,
            "reason": "no_vowel"
        }

    # ------------------------------------------
    # Thu tach am tiet
    # ------------------------------------------

    try:

        parts = parse_syllable(
            word
        )

    except Exception:

        return {
            "token": word,
            "valid": False,
            "reason": "parse_error"
        }

    # ------------------------------------------
    # Kiem tra cau truc parser tra ve
    # ------------------------------------------

    valid, reason = validate_parsed_parts(
        parts
    )

    if not valid:

        return {
            "token": word,
            "valid": False,
            "reason": reason,
            "parts": parts
        }

    # ------------------------------------------
    # Hop le
    # ------------------------------------------

    return {
        "token": word,
        "valid": True,
        "reason": "valid",
        "parts": parts
    }


# ==========================================================
# 12. TEST NHANH
# ==========================================================

if __name__ == "__main__":

    test_words = [

        # -------------------------------
        # CAC TU TIENG VIET HOP LE
        # -------------------------------

        "chạy",
        "chảy",
        "nước",
        "người",
        "trời",
        "thuyền",
        "lãnh",
        "lánh",
        "ánh",
        "anh",
        "hoa",
        "khoa",
        "loan",
        "nghiêng",
        "quang",
        "ban",
        "bang",
        "sang",

        # -------------------------------
        # CAC TOKEN KHONG HOP LE
        # -------------------------------

        "123",
        "2V",
        "vungınız",
        "@abc",
        "",
        "xyz",
        "bcd",
        "qza"
    ]

    print(
        "===== KIEM TRA TOKEN TIENG VIET ====="
    )

    so_hop_le = 0
    so_khong_hop_le = 0

    for word in test_words:

        result = classify_token(
            word
        )

        if result["valid"]:
            so_hop_le += 1
        else:
            so_khong_hop_le += 1

        print(
            f"{word!r:15} "
            f"-> valid={result['valid']} "
            f"| reason={result['reason']}"
        )

    print(
        "\n===== TONG KET ====="
    )

    print(
        "Hop le:",
        so_hop_le
    )

    print(
        "Khong hop le:",
        so_khong_hop_le
    )