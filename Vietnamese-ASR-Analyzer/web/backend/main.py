# -*- coding: utf-8 -*-

import json
import os

from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware



# =====================================================
# CONFIG
# =====================================================


BASE_DIR = Path(

    os.getenv(

        "ASR_DATASET_DIR",

        Path(__file__).resolve().parents[2] / "dataset"

    )

)


STAT_FILE = BASE_DIR / "error_statistics.json"

ANALYSIS_FILE = BASE_DIR / "sentence_analysis.json"





ALLOWED_ORIGINS = os.getenv(

    "CORS_ORIGINS",

    "http://localhost:5173,http://localhost:5174,http://localhost:3000"

).split(",")





STATUS_MAP = {


    "correct":
    "correct",


    "Đúng":
    "correct",



    "incorrect":
    "incorrect",


    "Sai":
    "incorrect",



    "failed":
    "failed",


    "Lỗi phân tích":
    "failed"

}






# =====================================================
# APP
# =====================================================


app = FastAPI(

    title="Vietnamese ASR Error Analyzer API"

)
# =====================================================
# AUDIO STATIC FILE
# =====================================================

AUDIO_DIR = BASE_DIR / "audio"


app.mount(
    "/audio",
    StaticFiles(directory=AUDIO_DIR),
    name="audio"
)






app.add_middleware(

    CORSMiddleware,


    allow_origins=ALLOWED_ORIGINS,


    allow_credentials=False,


    allow_methods=["GET"],


    allow_headers=["*"],

)







# =====================================================
# CACHE
# =====================================================


_json_cache: dict[Path, tuple[float, Any]] = {}



_index = {

    "src": None,

    "items": [],

    "by_audio": {}

}







# =====================================================
# LOAD JSON
# =====================================================


def load_json(path: Path):


    try:

        mtime = path.stat().st_mtime


    except FileNotFoundError:


        raise HTTPException(

            status_code=503,

            detail=f"Chưa có file {path.name}"

        )




    cached = _json_cache.get(path)



    if cached and cached[0] == mtime:


        return cached[1]




    try:


        with open(

            path,

            "r",

            encoding="utf-8"

        ) as f:


            data = json.load(f)



    except json.JSONDecodeError as e:



        raise HTTPException(

            status_code=500,

            detail=f"Lỗi JSON {path.name}: {e}"

        )




    _json_cache[path] = (

        mtime,

        data

    )



    return data







# =====================================================
# INDEX AUDIO
# =====================================================


def get_items():


    data = load_json(

        ANALYSIS_FILE

    )



    if _index["src"] is not data:


        items = data.get(

            "data",

            []

        )



        for item in items:


            item["status"] = STATUS_MAP.get(

                item.get("status"),

                "failed"

            )



        _index.update({

            "src": data,


            "items": items,


            "by_audio": {

                x.get("audio"): x

                for x in items

            }

        })




    return (

        _index["items"],

        _index["by_audio"]

    )







# =====================================================
# NUMBER CONVERT
# =====================================================


def _num(value) -> Optional[float]:


    try:

        return float(value)


    except:

        return None







# =====================================================
# HOME
# =====================================================


@app.get("/")

def home():


    return {


        "message":

        "Vietnamese ASR Error Analyzer API"

    }









# =====================================================
# STATISTICS
# =====================================================


@app.get("/api/statistics")

def statistics():


    stat = dict(

        load_json(STAT_FILE)

    )


    items, _ = get_items()





    wer_vals = [

        _num(x.get("wer"))

        for x in items

        if _num(x.get("wer")) is not None

    ]



    cer_vals = [

        _num(x.get("cer"))

        for x in items

        if _num(x.get("cer")) is not None

    ]






    # Corpus WER

    total_error = 0

    total_words = 0



    for x in items:


        wer = _num(

            x.get("wer")

        )


        words = len(

            str(

                x.get(

                    "ground_truth",

                    ""

                )

            ).split()

        )


        if wer is not None and words > 0:


            total_error += wer * words

            total_words += words







    def count(status):


        return sum(

            1

            for x in items

            if x["status"] == status

        )







    scored = [

        x

        for x in items

        if _num(x.get("wer")) is not None

    ]





    worst = max(

        scored,

        key=lambda x:

        _num(x.get("wer")),

        default=None

    )








    stat.update({



        "average_wer":

        round(

            sum(wer_vals)

            /

            len(wer_vals),

            4

        )

        if wer_vals else 0,





        "average_cer":

        round(

            sum(cer_vals)

            /

            len(cer_vals),

            4

        )

        if cer_vals else 0,





        "corpus_wer":

        round(

            total_error

            /

            total_words,

            4

        )

        if total_words else 0,





        "correct_sentence":

        count("correct"),




        "incorrect_sentence":

        count("incorrect"),





        "failed_sentence":

        count("failed"),





        "score_chart":

        [

            {

                "audio":

                x.get("audio"),


                "wer":

                _num(x.get("wer")) or 0,


                "cer":

                _num(x.get("cer")) or 0

            }


            for x in items

        ],






        "worst_audio":

        {

            "audio":

            worst.get("audio"),


            "wer":

            worst.get("wer"),


            "cer":

            worst.get("cer")

        }

        if worst else None



    })




    return stat







# =====================================================
# AUDIO LIST
# =====================================================


@app.get("/api/audio-list")

def audio_list(


    status: Optional[str] = Query(

        None,

        pattern="^(correct|incorrect|failed)$"

    ),


    q: Optional[str] = None,


    limit: Optional[int] = Query(

        None,

        ge=1,

        le=5000

    ),


    offset: int = Query(

        0,

        ge=0

    )


):



    items, _ = get_items()




    if status:


        items = [

            x

            for x in items

            if x["status"] == status

        ]





    if q:


        q = q.lower()



        items = [

            x

            for x in items

            if q in str(

                x.get("audio","")

            ).lower()

        ]







    total = len(items)



    page = (

        items[offset:offset+limit]

        if limit

        else items[offset:]

    )






    return {


        "total":

        total,



        "data":

        [

            {


                "audio":

                x.get("audio"),



                "wer":

                x.get("wer"),



                "cer":

                x.get("cer"),



                "status":

                x["status"],



                "errors":

                x.get(

                    "errors",

                    []

                )

            }


            for x in page

        ]

    }








# =====================================================
# AUDIO DETAIL
# =====================================================


@app.get("/api/audio-detail/{audio:path}")

def audio_detail(audio:str):


    _, by_audio = get_items()



    item = by_audio.get(audio)



    if item is None:


        raise HTTPException(

            status_code=404,

            detail="Audio not found"

        )



    return item