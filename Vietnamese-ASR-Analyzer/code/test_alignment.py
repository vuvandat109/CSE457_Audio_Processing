import jiwer

ground_truth = "Ở cái nơi rừng thiêng nước độc này"
prediction = "Um có vungınız hab kh"

output = jiwer.process_words(
    ground_truth,
    prediction
)

print("===== TONG QUAN =====")
print("WER:", output.wer)
print("Substitutions:", output.substitutions)
print("Deletions:", output.deletions)
print("Insertions:", output.insertions)
print("Hits:", output.hits)

print("\n===== ALIGNMENT =====")

for chunk in output.alignments[0]:

    ref_words = output.references[0][
        chunk.ref_start_idx:chunk.ref_end_idx
    ]

    hyp_words = output.hypotheses[0][
        chunk.hyp_start_idx:chunk.hyp_end_idx
    ]

    print(
        f"{chunk.type.upper():12} | "
        f"REF: {' '.join(ref_words):25} | "
        f"HYP: {' '.join(hyp_words)}"
    )