import json
import sys


sys.path.append(
    r"E:\ASR_Project\web\backend"
)


from vietnamese_phoneme import split_syllable




WORD_FILE = r"E:\ASR_Project\dataset\vietnamese_words.txt"


OUTPUT_FILE = r"E:\ASR_Project\dataset\vietnamese_dictionary.json"





# đọc danh sách từ

with open(
    WORD_FILE,
    "r",
    encoding="utf-8"
) as f:

    words = [

        x.strip()

        for x in f.readlines()

        if x.strip()

    ]



print(
    "Total words:",
    len(words)
)





dictionary = {}



for word in words:


    try:


        result = split_syllable(
            word
        )


        dictionary[word] = {


            "initial":

            result["initial"],



            "nucleus":

            result["nucleus"],



            "final":

            result["final"],



            "tone":

            result["tone"]

        }


        print(
            "[OK]",
            word
        )


    except Exception as e:


        print(
            "[ERROR]",
            word,
            e
        )






with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:


    json.dump(

        dictionary,

        f,

        ensure_ascii=False,

        indent=2

    )




print("===================")

print("DONE")

print(
    OUTPUT_FILE
)

print("===================")