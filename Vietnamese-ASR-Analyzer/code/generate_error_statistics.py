# -*- coding: utf-8 -*-

"""
generate_error_statistics.py

Vietnamese ASR Error Statistics V13.3

Input:
sentence_analysis.json

Output:
error_statistics.json
"""


import json
from pathlib import Path
from collections import Counter, defaultdict





# =====================================================
# PATH
# =====================================================


ROOT = Path(__file__).resolve().parent


INPUT_FILE = (

    ROOT.parent

    /

    "dataset"

    /

    "sentence_analysis.json"

)



OUTPUT_FILE = (

    ROOT.parent

    /

    "dataset"

    /

    "error_statistics.json"

)






# =====================================================
# LOAD JSON
# =====================================================


print(

    "Loading sentence analysis..."

)



with open(

    INPUT_FILE,

    "r",

    encoding="utf-8"

) as f:


    data = json.load(f)






samples = data["data"]






# =====================================================
# COUNTER
# =====================================================


error_distribution = Counter()



phoneme_detail = {


    "initial": {


        "type":

        Counter(),



        "confusion":

        Counter()

    },



    "nucleus": {


        "confusion":

        Counter()

    },



    "final": {


        "type":

        Counter(),



        "confusion":

        Counter()

    },



    "tone": {


        "confusion":

        Counter()

    }


}







total_error = 0







# =====================================================
# PROCESS
# =====================================================


for sample in samples:



    # -------------------------
    # sentence errors
    # -------------------------


    for err in sample.get(

        "errors",

        []

    ):



        if err == "equal":

            continue



        error_distribution[err] += 1

        total_error += 1






    # -------------------------
    # word phoneme detail
    # -------------------------


    for word in sample.get(

        "word_analysis",

        []

    ):



        detail = word.get(

            "detail"

        )



        if not detail:

            continue






        # ======================
        # INITIAL
        # ======================


        initial = detail.get(

            "initial"

        )



        if initial:



            if not initial.get(

                "correct",

                True

            ):



                phoneme_detail["initial"]["type"][

                    "substitution"

                ] += 1



                key = (

                    str(

                        initial.get(

                            "reference",

                            ""

                        )

                    )

                    +

                    " -> "

                    +

                    str(

                        initial.get(

                            "prediction",

                            ""

                        )

                    )

                )



                phoneme_detail["initial"]["confusion"][key] += 1








        # ======================
        # NUCLEUS
        # ======================


        nucleus = detail.get(

            "nucleus"

        )



        if nucleus:



            if not nucleus.get(

                "correct",

                True

            ):



                key = (

                    str(

                        nucleus.get(

                            "reference",

                            ""

                        )

                    )

                    +

                    " -> "

                    +

                    str(

                        nucleus.get(

                            "prediction",

                            ""

                        )

                    )

                )



                phoneme_detail["nucleus"]["confusion"][key] += 1






        # ======================
        # FINAL
        # ======================


        final = detail.get(

            "final"

        )



        if final:



            if not final.get(

                "correct",

                True

            ):



                phoneme_detail["final"]["type"][

                    "substitution"

                ] += 1



                key = (

                    str(

                        final.get(

                            "reference",

                            ""

                        )

                    )

                    +

                    " -> "

                    +

                    str(

                        final.get(

                            "prediction",

                            ""

                        )

                    )

                )



                phoneme_detail["final"]["confusion"][key] += 1








        # ======================
        # TONE
        # ======================


        tone = detail.get(

            "tone"

        )



        if tone:



            if not tone.get(

                "correct",

                True

            ):



                key = (

                    str(

                        tone.get(

                            "reference",

                            ""

                        )

                    )

                    +

                    " -> "

                    +

                    str(

                        tone.get(

                            "prediction",

                            ""

                        )

                    )

                )



                phoneme_detail["tone"]["confusion"][key] += 1







# =====================================================
# CONVERT COUNTER
# =====================================================


def convert(obj):


    if isinstance(

        obj,

        Counter

    ):


        return dict(obj)



    if isinstance(

        obj,

        dict

    ):


        return {

            k:

            convert(v)

            for k,v in obj.items()

        }



    return obj






# =====================================================
# OUTPUT
# =====================================================


output = {


    "total_audio":

    len(samples),



    "total_error":

    total_error,



    "error_distribution":

    convert(

        error_distribution

    ),



    "phoneme_detail":

    convert(

        phoneme_detail

    )

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







print("==========================")

print("DONE")

print(

    "Total audio:",

    len(samples)

)

print(

    "Total error:",

    total_error

)

print(

    "Saved:",

    OUTPUT_FILE

)

print("==========================")