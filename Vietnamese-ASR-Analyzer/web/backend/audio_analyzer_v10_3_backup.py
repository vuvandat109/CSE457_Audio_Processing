# -*- coding: utf-8 -*-

# =====================================================
# audio_analyzer.py
# Vietnamese ASR Error Analyzer V10.3
# Text Normalization + Phoneme Analysis
# =====================================================


import re
import unicodedata
import jiwer


from vietnamese_phoneme import analyze_word






# =====================================================
# TEXT NORMALIZATION
# =====================================================


def normalize_text(text):


    text = unicodedata.normalize(
        "NFC",
        str(text)
    )


    text = text.lower()



    return text.strip()







def normalize_word(word):


    word = unicodedata.normalize(
        "NFC",
        str(word)
    )


    word = word.lower()



    # bỏ dấu câu

    word = re.sub(

        r"[^\wà-ỹđ]",

        "",

        word

    )



    return word






def normalize_sentence(text):


    words = []


    for w in text.split():

        clean = normalize_word(w)


        if clean:

            words.append(clean)



    return " ".join(words)







# =====================================================
# WER / CER
# =====================================================


def calculate_score(
        reference,
        prediction
):


    reference_clean = normalize_sentence(
        reference
    )


    prediction_clean = normalize_sentence(
        prediction
    )



    wer = jiwer.wer(

        reference_clean,

        prediction_clean

    )



    cer = jiwer.cer(

        reference_clean,

        prediction_clean

    )



    return {


        "wer":

        round(
            wer,
            4
        ),



        "cer":

        round(
            cer,
            4
        )

    }









# =====================================================
# PHÂN TÍCH 1 TỪ
# =====================================================


def detect_word_error(
        reference,
        prediction
):


    detail = analyze_word(

        reference,

        prediction

    )



    errors = []




    if not detail["initial"]["correct"]:


        errors.append(

            "initial_consonant_error"

        )




    if not detail["nucleus"]["correct"]:


        errors.append(

            "nucleus_error"

        )





    if not detail["final"]["correct"]:


        errors.append(

            "final_consonant_error"

        )





    if not detail["tone"]["correct"]:


        errors.append(

            "tone_error"

        )



    return errors, detail











# =====================================================
# KIỂM TRA LỖI TOÀN CÂU
# =====================================================


def simple_error_check(
        reference,
        prediction
):


    errors = []



    ref_words = [

        normalize_word(w)

        for w in reference.split()

    ]



    hyp_words = [

        normalize_word(w)

        for w in prediction.split()

    ]




    if ref_words == hyp_words:


        return errors






    if len(ref_words) != len(hyp_words):


        errors.append(

            "multi_component_error"

        )



    max_len = max(

        len(ref_words),

        len(hyp_words)

    )





    for i in range(max_len):


        if i >= len(ref_words):

            continue



        if i >= len(hyp_words):

            continue





        r = ref_words[i]

        h = hyp_words[i]





        if r != h:


            word_errors, _ = detect_word_error(

                r,

                h

            )


            errors.extend(

                word_errors

            )





    return list(set(errors))












# =====================================================
# PHÂN TÍCH CHI TIẾT TỪNG TỪ
# =====================================================


def analyze_sentence_phoneme(
        reference,
        prediction
):


    ref_words = [

        normalize_word(w)

        for w in reference.split()

    ]



    hyp_words = [

        normalize_word(w)

        for w in prediction.split()

    ]





    result = []



    max_len = max(

        len(ref_words),

        len(hyp_words)

    )





    for i in range(max_len):


        ref = (

            ref_words[i]

            if i < len(ref_words)

            else ""

        )



        hyp = (

            hyp_words[i]

            if i < len(hyp_words)

            else ""

        )






        if ref and hyp and ref != hyp:



            try:


                detail = analyze_word(

                    ref,

                    hyp

                )



            except Exception as e:


                detail = {


                    "error":

                    str(e)

                }






            result.append({


                "reference":

                ref,



                "prediction":

                hyp,



                "detail":

                detail



            })




    return result












# =====================================================
# PHÂN TÍCH 1 AUDIO
# =====================================================


def analyze_result(
        audio,
        reference,
        prediction
):



    score = calculate_score(

        reference,

        prediction

    )




    errors = simple_error_check(

        reference,

        prediction

    )




    word_analysis = analyze_sentence_phoneme(

        reference,

        prediction

    )






    return {



        "audio":

        audio,




        "ground_truth":

        normalize_sentence(reference),




        "prediction":

        normalize_sentence(prediction),




        "wer":

        score["wer"],




        "cer":

        score["cer"],




        "status":


        "Đúng"

        if len(errors)==0

        else

        "Sai",




        "errors":

        errors,




        "word_analysis":

        word_analysis



    }