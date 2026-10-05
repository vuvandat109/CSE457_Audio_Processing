import unicodedata
import re


# =========================
# 1. CAC DAU THANH TIENG VIET
# =========================

TONE_MARKS = {
    "\u0300": "huyen",
    "\u0301": "sac",
    "\u0309": "hoi",
    "\u0303": "nga",
    "\u0323": "nang"
}


# =========================
# 2. PHU AM DAU
# =========================

INITIALS = [
    "ngh",
    "ng",
    "gh",
    "gi",
    "kh",
    "ph",
    "th",
    "tr",
    "ch",
    "nh",
    "qu",
    "b",
    "c",
    "d",
    "đ",
    "g",
    "h",
    "k",
    "l",
    "m",
    "n",
    "p",
    "q",
    "r",
    "s",
    "t",
    "v",
    "x"
]


# =========================
# 3. AM CUOI
# =========================

CODAS = [
    "ng",
    "nh",
    "ch",
    "c",
    "m",
    "n",
    "p",
    "t",
    "i",
    "y",
    "o",
    "u"
]


# =========================
# 4. NGUYEN AM CO THE LA AM DEM
# =========================

MEDIALS = [
    "o",
    "u"
]


def normalize_word(word):
    """
    Chuan hoa Unicode va dua ve chu thuong.
    """

    word = str(word).strip().lower()
    word = unicodedata.normalize("NFC", word)

    word = re.sub(
        r"[^a-zA-ZÀ-ỹđĐ]",
        "",
        word
    )

    return word


def get_tone(word):
    """
    Lay thanh dieu cua am tiet.

    Ket qua:
    ngang
    sac
    huyen
    hoi
    nga
    nang
    """

    word = normalize_word(word)

    decomposed = unicodedata.normalize(
        "NFD",
        word
    )

    for char in decomposed:

        if char in TONE_MARKS:
            return TONE_MARKS[char]

    return "ngang"


def remove_tone(word):
    """
    Bo dau thanh nhung giu nguyen chat luong nguyen am.

    VD:
    chạy -> chay
    chảy -> chay

    nước -> nươc
    """

    word = normalize_word(word)

    decomposed = unicodedata.normalize(
        "NFD",
        word
    )

    result = []

    for char in decomposed:

        if char in TONE_MARKS:
            continue

        result.append(char)

    return unicodedata.normalize(
        "NFC",
        "".join(result)
    )


def get_initial(word):
    """
    Tim phu am dau theo longest-prefix.
    """

    word = remove_tone(word)

    for initial in sorted(
        INITIALS,
        key=len,
        reverse=True
    ):

        if word.startswith(initial):
            return initial

    return ""


def remove_initial(word, initial):
    """
    Bo phu am dau khoi am tiet.
    """

    word = remove_tone(word)

    if initial and word.startswith(initial):
        return word[len(initial):]

    return word


def get_coda(rhyme):
    """
    Tim am cuoi.

    Luu y:
    i, y, o, u co the dong vai tro ban nguyen am cuoi.
    """

    for coda in sorted(
        CODAS,
        key=len,
        reverse=True
    ):

        if (
            rhyme.endswith(coda)
            and len(rhyme) > len(coda)
        ):
            return coda

    return ""


def remove_coda(rhyme, coda):

    if coda and rhyme.endswith(coda):
        return rhyme[:-len(coda)]

    return rhyme


def split_medial_nucleus(core):
    """
    Tach am dem va am chinh theo quy tac heuristic co kiem soat.

    VD:
    hoa -> medial=o, nucleus=a
    khoa -> medial=o, nucleus=a
    loan -> medial=o, nucleus=a

    Nhung:
    ua, uo... khong phai luc nao cung la am dem.
    """

    if len(core) <= 1:
        return "", core

    # Truong hop o/u dung truoc mot nguyen am khac
    # thi co kha nang la am dem
    first = core[0]

    if first in MEDIALS:
        return first, core[1:]

    return "", core


def parse_syllable(word):
    """
    Phan tich mot am tiet tieng Viet.

    Output:
    {
        word,
        base,
        initial,
        medial,
        nucleus,
        coda,
        tone
    }
    """

    original = normalize_word(word)

    tone = get_tone(original)
    base = remove_tone(original)

    initial = get_initial(original)

    rhyme = remove_initial(
        original,
        initial
    )

    coda = get_coda(rhyme)

    core = remove_coda(
        rhyme,
        coda
    )

    medial, nucleus = split_medial_nucleus(
        core
    )

    return {
        "word": original,
        "base": base,
        "initial": initial,
        "medial": medial,
        "nucleus": nucleus,
        "coda": coda,
        "tone": tone
    }


if __name__ == "__main__":

    tests = [
        "chạy",
        "chảy",
        "già",
        "giả",
        "nước",
        "người",
        "trời",
        "khoa",
        "loan",
        "anh",
        "ánh",
        "lãnh",
        "lánh",
        "thuyền",
        "quang",
        "nghiêng"
    ]

    for word in tests:

        result = parse_syllable(word)

        print("\n====================")
        print("WORD   :", word)
        print("BASE   :", result["base"])
        print("INITIAL:", result["initial"])
        print("MEDIAL :", result["medial"])
        print("NUCLEUS:", result["nucleus"])
        print("CODA   :", result["coda"])
        print("TONE   :", result["tone"])