import pandas as pd
from collections import Counter


input_file = r"E:\ASR_Project\dataset\vietnamese_error_analysis.csv"

output_tone = r"E:\ASR_Project\dataset\tone_confusion.csv"
output_initial = r"E:\ASR_Project\dataset\initial_confusion.csv"
output_medial = r"E:\ASR_Project\dataset\medial_confusion.csv"
output_nucleus = r"E:\ASR_Project\dataset\nucleus_confusion.csv"
output_coda = r"E:\ASR_Project\dataset\coda_confusion.csv"


df = pd.read_csv(
    input_file,
    encoding="utf-8-sig"
)


def safe_value(value):

    if pd.isna(value):
        return ""

    return str(value).strip()


def build_confusion(
    ref_column,
    hyp_column
):

    counter = Counter()

    for _, row in df.iterrows():

        ref = safe_value(
            row[ref_column]
        )

        hyp = safe_value(
            row[hyp_column]
        )

        # Chi dem khi thanh phan thuc su thay doi
        if ref != hyp:

            ref_show = (
                ref if ref != ""
                else "∅"
            )

            hyp_show = (
                hyp if hyp != ""
                else "∅"
            )

            counter[
                (ref_show, hyp_show)
            ] += 1

    result = []

    for (
        ref,
        hyp
    ), count in counter.most_common():

        result.append({
            "reference": ref,
            "hypothesis": hyp,
            "count": count
        })

    return pd.DataFrame(result)


# ==========================
# TONE
# ==========================

tone_df = build_confusion(
    "ref_tone",
    "hyp_tone"
)

tone_df.to_csv(
    output_tone,
    index=False,
    encoding="utf-8-sig"
)


# ==========================
# INITIAL
# ==========================

initial_df = build_confusion(
    "ref_initial",
    "hyp_initial"
)

initial_df.to_csv(
    output_initial,
    index=False,
    encoding="utf-8-sig"
)


# ==========================
# MEDIAL
# ==========================

medial_df = build_confusion(
    "ref_medial",
    "hyp_medial"
)

medial_df.to_csv(
    output_medial,
    index=False,
    encoding="utf-8-sig"
)


# ==========================
# NUCLEUS
# ==========================

nucleus_df = build_confusion(
    "ref_nucleus",
    "hyp_nucleus"
)

nucleus_df.to_csv(
    output_nucleus,
    index=False,
    encoding="utf-8-sig"
)


# ==========================
# CODA
# ==========================

coda_df = build_confusion(
    "ref_coda",
    "hyp_coda"
)

coda_df.to_csv(
    output_coda,
    index=False,
    encoding="utf-8-sig"
)


print(
    "===== CONFUSION ANALYSIS ====="
)


def show_top(
    title,
    dataframe,
    n=10
):

    print(
        f"\n--- {title} ---"
    )

    if len(dataframe) == 0:

        print(
            "Khong co loi"
        )

        return

    for _, row in dataframe.head(n).iterrows():

        print(
            f"{row['reference']} "
            f"-> "
            f"{row['hypothesis']} "
            f": {row['count']}"
        )


show_top(
    "TONE",
    tone_df
)

show_top(
    "INITIAL",
    initial_df
)

show_top(
    "MEDIAL",
    medial_df
)

show_top(
    "NUCLEUS",
    nucleus_df
)

show_top(
    "CODA",
    coda_df
)


print(
    "\nDa luu cac file confusion tai:"
)

print(
    output_tone
)

print(
    output_initial
)

print(
    output_medial
)

print(
    output_nucleus
)

print(
    output_coda
)