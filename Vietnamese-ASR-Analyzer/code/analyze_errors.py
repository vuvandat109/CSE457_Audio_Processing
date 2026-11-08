import pandas as pd
import jiwer

from text_normalizer import normalize_vietnamese_text


input_file = r"E:\ASR_Project\dataset\asr_results.csv"
output_file = r"E:\ASR_Project\dataset\error_analysis.csv"

df = pd.read_csv(input_file, encoding="utf-8-sig")

results = []

for _, row in df.iterrows():

    audio = row["audio"]
    ground_truth = str(row["ground_truth"])
    prediction = str(row["prediction"])

    gt = normalize_vietnamese_text(ground_truth)
    pred = normalize_vietnamese_text(prediction)

    output = jiwer.process_words(gt, pred)

    # Thong ke tong
    substitutions = output.substitutions
    deletions = output.deletions
    insertions = output.insertions
    hits = output.hits

    # Lay chi tiet alignment
    alignment_details = []

    for chunk in output.alignments[0]:

        ref_words = output.references[0][
            chunk.ref_start_idx:chunk.ref_end_idx
        ]

        hyp_words = output.hypotheses[0][
            chunk.hyp_start_idx:chunk.hyp_end_idx
        ]

        alignment_details.append({
            "type": chunk.type,
            "reference": " ".join(ref_words),
            "hypothesis": " ".join(hyp_words)
        })

    results.append({
        "audio": audio,
        "ground_truth": ground_truth,
        "prediction": prediction,

        "wer": output.wer,

        "substitutions": substitutions,
        "deletions": deletions,
        "insertions": insertions,
        "hits": hits,

        "alignment": str(alignment_details)
    })


result_df = pd.DataFrame(results)

result_df.to_csv(
    output_file,
    index=False,
    encoding="utf-8-sig"
)


print("===== PHAN TICH LOI HOAN TAT =====")

print("So cau:", len(result_df))

print("\nTong Substitution:",
      result_df["substitutions"].sum())

print("Tong Deletion:",
      result_df["deletions"].sum())

print("Tong Insertion:",
      result_df["insertions"].sum())

print("Tong Hits:",
      result_df["hits"].sum())

print("\nDa luu:")
print(output_file)