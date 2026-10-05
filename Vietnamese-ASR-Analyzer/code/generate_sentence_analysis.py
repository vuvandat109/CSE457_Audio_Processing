# -*- coding: utf-8 -*-

"""
generate_sentence_analysis.py
Vietnamese ASR Sentence Analysis V13.2 FINAL

CSV
 |
word_alignment
 |
simple_error_check
 |
analyze_sentence_phoneme
 |
sentence_analysis.json
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


def analyze_row(row):


    audio = normalize(

        row.get(

            "audio"

        )

    )



    reference = normalize(

        row.get(

            "ground_truth"

        )

    )



    prediction = normalize(

        row.get(

            "prediction"

        )

    )




    result = {


        "audio":

        audio,



        "ground_truth":

        reference,



        "prediction":

        prediction,



        "analysis_failed":

        False

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


            "wer":

            score["wer"],



            "cer":

            score["cer"],



            "status":

            (

                "Đúng"

                if len(errors)==0

                else

                "Sai"

            ),



            "errors":

            errors,



            "alignment":

            alignment,



            "word_analysis":

            word_analysis


        })





    except Exception as e:



        log.exception(

            "Analysis failed: %s",

            audio

        )



        result.update({


            "analysis_failed":

            True,



            "analysis_error":

            str(e),



            "status":

            "Lỗi phân tích",



            "errors":

            [

                "analysis_failed"

            ],



            "alignment":

            [],



            "word_analysis":

            [],



            "wer":

            None,



            "cer":

            None


        })





    return result







# =====================================================
# MAIN
# =====================================================


def main():



    logging.basicConfig(

        level=logging.INFO

    )



    parser = argparse.ArgumentParser()



    parser.add_argument(

        "--input",

        type=Path,

        default=

        ROOT.parent /

        "dataset" /

        "asr_results.csv"

    )




    parser.add_argument(

        "--output",

        type=Path,

        default=

        ROOT.parent /

        "dataset" /

        "sentence_analysis.json"

    )



    args = parser.parse_args()





    print(

        "Loading dataset..."

    )





    df = pd.read_csv(

        args.input,

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

            f"Missing columns: {missing}"

        )







    print(

        "ASR samples:",

        len(df)

    )







    results=[]



    for row in tqdm(

        df.to_dict("records"),

        total=len(df)

    ):



        results.append(

            analyze_row(row)

        )







    failed = sum(

        1

        for x in results

        if x["analysis_failed"]

    )







    output = {


        "total_audio":

        len(results),



        "analysis_failed":

        failed,



        "data":

        results


    }






    args.output.parent.mkdir(

        parents=True,

        exist_ok=True

    )





    with open(

        args.output,

        "w",

        encoding="utf-8"

    ) as f:


        json.dump(

            output,

            f,

            ensure_ascii=False,

            indent=2

        )







    print("==========================")

    print(

        "DONE"

    )


    print(

        "Total:",

        len(results)

    )


    print(

        "Failed:",

        failed

    )


    print(

        "Saved:",

        args.output

    )


    print("==========================")






if __name__ == "__main__":

    main()