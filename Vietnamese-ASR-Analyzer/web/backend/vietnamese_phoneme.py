# -*- coding: utf-8 -*-

# =====================================================
# vietnamese_phoneme.py
# Vietnamese ASR Phoneme Analyzer V9.2
# Dictionary First + Unicode Normalization
# =====================================================


import unicodedata

from vietnamese_dictionary import lookup_word





# =====================================================
# NORMALIZE
# =====================================================

def normalize_text(text):

    return unicodedata.normalize(
        "NFC",
        str(text)
        .lower()
        .strip()
    )






# =====================================================
# TONE MAP
# =====================================================


TONE_MAP = {

    "á":"sắc",
    "à":"huyền",
    "ả":"hỏi",
    "ã":"ngã",
    "ạ":"nặng",


    "ắ":"sắc",
    "ằ":"huyền",
    "ẳ":"hỏi",
    "ẵ":"ngã",
    "ặ":"nặng",


    "ấ":"sắc",
    "ầ":"huyền",
    "ẩ":"hỏi",
    "ẫ":"ngã",
    "ậ":"nặng",


    "é":"sắc",
    "è":"huyền",
    "ẻ":"hỏi",
    "ẽ":"ngã",
    "ẹ":"nặng",


    "ế":"sắc",
    "ề":"huyền",
    "ể":"hỏi",
    "ễ":"ngã",
    "ệ":"nặng",


    "í":"sắc",
    "ì":"huyền",
    "ỉ":"hỏi",
    "ĩ":"ngã",
    "ị":"nặng",


    "ó":"sắc",
    "ò":"huyền",
    "ỏ":"hỏi",
    "õ":"ngã",
    "ọ":"nặng",


    "ố":"sắc",
    "ồ":"huyền",
    "ổ":"hỏi",
    "ỗ":"ngã",
    "ộ":"nặng",


    "ớ":"sắc",
    "ờ":"huyền",
    "ở":"hỏi",
    "ỡ":"ngã",
    "ợ":"nặng",


    "ú":"sắc",
    "ù":"huyền",
    "ủ":"hỏi",
    "ũ":"ngã",
    "ụ":"nặng",


    "ứ":"sắc",
    "ừ":"huyền",
    "ử":"hỏi",
    "ữ":"ngã",
    "ự":"nặng",


    "ý":"sắc",
    "ỳ":"huyền",
    "ỷ":"hỏi",
    "ỹ":"ngã",
    "ỵ":"nặng"

}







# =====================================================
# GET TONE
# =====================================================


def get_tone(word):

    word = normalize_text(word)


    for char in word:

        if char in TONE_MAP:

            return TONE_MAP[char]


    return "ngang"







# =====================================================
# REMOVE TONE
# =====================================================


def remove_tone(word):

    word = normalize_text(word)


    table = str.maketrans(

        "áàảãạ"
        "ắằẳẵặ"
        "ấầẩẫậ"
        "éèẻẽẹ"
        "ếềểễệ"
        "íìỉĩị"
        "óòỏõọ"
        "ốồổỗộ"
        "ớờởỡợ"
        "úùủũụ"
        "ứừửữự"
        "ýỳỷỹỵ",


        "aaaaa"
        "ăăăăă"
        "âââââ"
        "eeeee"
        "êêêêê"
        "iiiii"
        "ooooo"
        "ôôôôô"
        "ơơơơơ"
        "uuuuu"
        "ưưưưư"
        "yyyyy"

    )


    return word.translate(table)








# =====================================================
# FALLBACK RULE
# =====================================================


INITIALS = [

    "ngh",
    "ch",
    "gh",
    "nh",
    "th",
    "tr",
    "ph",
    "kh",
    "qu",
    "gi",
    "ng",

    "đ",

    "b",
    "c",
    "d",
    "g",
    "h",
    "k",
    "l",
    "m",
    "n",
    "p",
    "r",
    "s",
    "t",
    "v",
    "x"

]




FINALS = [

    "ng",
    "nh",
    "ch",
    "m",
    "n",
    "p",
    "t",
    "c"

]







def split_syllable(word):


    clean = remove_tone(word)


    result = {


        "initial":"",
        "nucleus":"",
        "final":"",
        "tone":get_tone(word)

    }




    for i in INITIALS:


        if clean.startswith(i):

            result["initial"] = i

            clean = clean[len(i):]

            break





    for f in FINALS:


        if clean.endswith(f):

            result["final"] = f

            clean = clean[:-len(f)]

            break





    result["nucleus"] = clean


    return result







# =====================================================
# DICTIONARY FIRST
# =====================================================


def get_word_phoneme(word):


    word = normalize_text(word)



    data = lookup_word(word)



    if data is not None:


        return {


            "initial":
            normalize_text(data["initial"]),



            "nucleus":
            normalize_text(data["nucleus"]),



            "final":
            normalize_text(data["final"]),



            "tone":
            data["tone"]

        }




    return split_syllable(word)








# =====================================================
# ANALYZE WORD
# =====================================================


def analyze_word(reference, prediction):


    reference = normalize_text(reference)

    prediction = normalize_text(prediction)



    ref = get_word_phoneme(reference)

    hyp = get_word_phoneme(prediction)



    return {


        "word": reference,


        "prediction": prediction,



        "initial":{

            "reference":ref["initial"],

            "prediction":hyp["initial"],

            "correct":
            ref["initial"] == hyp["initial"]

        },



        "nucleus":{

            "reference":ref["nucleus"],

            "prediction":hyp["nucleus"],

            "correct":
            ref["nucleus"] == hyp["nucleus"]

        },



        "final":{

            "reference":ref["final"],

            "prediction":hyp["final"],

            "correct":
            ref["final"] == hyp["final"]

        },



        "tone":{

            "reference":ref["tone"],

            "prediction":hyp["tone"],

            "correct":
            ref["tone"] == hyp["tone"]

        }


    }