import json
import os
from pathlib import Path



# =====================================
# FILE DICTIONARY
# =====================================


DATASET_DIR = Path(os.getenv("ASR_DATASET_DIR", str(Path(__file__).resolve().parents[2] / "dataset")))
DICT_FILE = Path(os.getenv("ASR_DICTIONARY_FILE", str(DATASET_DIR / "vietnamese_dictionary_clean.json")))





# =====================================
# LOAD DICTIONARY
# =====================================


def load_dictionary():


    if not os.path.exists(DICT_FILE):

        print(
            "Dictionary not found"
        )

        return {}



    with open(

        DICT_FILE,

        "r",

        encoding="utf-8"

    ) as f:


        return json.load(f)







# =====================================
# GLOBAL DATA
# =====================================


VIETNAMESE_DICT = load_dictionary()







# =====================================
# LOOKUP WORD
# =====================================


def lookup_word(word):


    word = word.lower().strip()



    return VIETNAMESE_DICT.get(

        word,

        None

    )