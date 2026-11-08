from pathlib import Path
DATASET_DIR = Path(__file__).resolve().parents[1] / "dataset"

import json


INPUT = str(DATASET_DIR / "vietnamese_dictionary.json")

OUTPUT = str(DATASET_DIR / "vietnamese_dictionary_clean.json")



with open(
    INPUT,
    "r",
    encoding="utf-8"
) as f:

    data = json.load(f)



clean = {}



for word, phoneme in data.items():


    # bỏ token quá ngắn

    if len(word) <= 1:

        continue



    # bỏ từ không có âm chính

    if phoneme["nucleus"] == "":

        continue



    clean[word] = phoneme





with open(
    OUTPUT,
    "w",
    encoding="utf-8"
) as f:


    json.dump(
        clean,
        f,
        ensure_ascii=False,
        indent=2
    )



print("================")

print("Before:", len(data))

print("After :", len(clean))

print("Saved:")

print(OUTPUT)

print("================")
