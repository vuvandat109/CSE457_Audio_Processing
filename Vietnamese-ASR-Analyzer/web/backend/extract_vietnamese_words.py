import pandas as pd
import re


INPUT_FILE = (
    r"E:\ASR_Project\dataset\validated.tsv"
)


OUTPUT_FILE = (
    r"E:\ASR_Project\dataset\vietnamese_words.txt"
)



print("Loading dataset...")


df = pd.read_csv(
    INPUT_FILE,
    sep="\t",
    encoding="utf-8"
)


print(
    "Samples:",
    len(df)
)



words = set()



for sentence in df["sentence"]:


    if pd.isna(sentence):

        continue


    sentence = sentence.lower()



    tokens = re.findall(
        r"[a-zà-ỹđ]+",
        sentence
    )


    for w in tokens:

        words.add(w)




print(
    "Unique words:",
    len(words)
)



with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:


    for w in sorted(words):

        f.write(
            w+"\n"
        )



print("================")

print("DONE")

print(
    OUTPUT_FILE
)

print("================")