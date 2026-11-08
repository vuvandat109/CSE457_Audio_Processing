import json
import unicodedata



DICT_FILE = (
    r"E:\ASR_Project\dataset\vietnamese_dictionary.json"
)



with open(
    DICT_FILE,
    "r",
    encoding="utf-8"
) as f:

    dictionary = json.load(f)



print("======================")
print("Dictionary quality")
print("======================")



total = len(dictionary)

print(
    "Total words:",
    total
)



no_nucleus = []

no_tone = []

unicode_error = []

short_words = []





for word, data in dictionary.items():


    # kiểm tra Unicode


    try:

        unicodedata.normalize(
            "NFC",
            word
        )


    except:


        unicode_error.append(word)




    # không có âm chính


    if data["nucleus"] == "":

        no_nucleus.append(word)



    # không có tone


    if data["tone"] == "":

        no_tone.append(word)




    # từ quá ngắn


    if len(word) <= 1:

        short_words.append(word)





print()

print(
    "No nucleus:",
    len(no_nucleus)
)

print(no_nucleus[:20])



print()

print(
    "No tone:",
    len(no_tone)
)

print(no_tone[:20])



print()

print(
    "Unicode error:",
    len(unicode_error)
)

print(unicode_error[:20])



print()

print(
    "Short words:",
    len(short_words)
)

print(short_words[:50])



print("======================")
print("DONE")
print("======================")