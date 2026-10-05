import pandas as pd
import jiwer

from text_normalizer import normalize_vietnamese_text
from vietnamese_error_analyzer import analyze_word_error


input_file = r"E:\ASR_Project\dataset\asr_results.csv"
output_file = r"E:\ASR_Project\dataset\vietnamese_error_analysis.csv"


df = pd.read_csv(
    input_file,
    encoding="utf-8-sig"
)


results = []


error_counts = {
    "tone_error": 0,
    "initial_consonant_error": 0,
    "medial_error": 0,
    "nucleus_error": 0,
    "final_consonant_error": 0,
    "multi_component_error": 0,
    "non_vietnamese_token": 0,
    "invalid_reference_token": 0,
    "unknown": 0
}


for _, row in df.iterrows():

    audio = row["audio"]

    ground_truth = str(
        row["ground_truth"]
    )

    prediction = str(
        row["prediction"]
    )


    gt = normalize_vietnamese_text(
        ground_truth
    )

    pred = normalize_vietnamese_text(
        prediction
    )


    output = jiwer.process_words(
        gt,
        pred
    )


    for chunk in output.alignments[0]:

        if chunk.type != "substitute":
            continue


        ref_words = output.references[0][
            chunk.ref_start_idx:
            chunk.ref_end_idx
        ]


        hyp_words = output.hypotheses[0][
            chunk.hyp_start_idx:
            chunk.hyp_end_idx
        ]


        # ==================================================
        # Truong hop so luong tu bang nhau
        # ==================================================

        if len(ref_words) == len(hyp_words):

            for ref_word, hyp_word in zip(
                ref_words,
                hyp_words
            ):

                analysis = analyze_word_error(
                    ref_word,
                    hyp_word
                )


                error_type = analysis[
                    "error_type"
                ]


                if error_type in error_counts:

                    error_counts[
                        error_type
                    ] += 1


                ref_parts = analysis.get(
                    "reference"
                )

                hyp_parts = analysis.get(
                    "hypothesis"
                )


                # ------------------------------------------
                # Lay thong tin reference
                # ------------------------------------------

                if ref_parts is not None:

                    ref_initial = ref_parts[
                        "initial"
                    ]

                    ref_medial = ref_parts[
                        "medial"
                    ]

                    ref_nucleus = ref_parts[
                        "nucleus"
                    ]

                    ref_coda = ref_parts[
                        "coda"
                    ]

                    ref_tone = ref_parts[
                        "tone"
                    ]

                else:

                    ref_initial = ""
                    ref_medial = ""
                    ref_nucleus = ""
                    ref_coda = ""
                    ref_tone = ""


                # ------------------------------------------
                # Lay thong tin hypothesis
                # ------------------------------------------

                if hyp_parts is not None:

                    hyp_initial = hyp_parts[
                        "initial"
                    ]

                    hyp_medial = hyp_parts[
                        "medial"
                    ]

                    hyp_nucleus = hyp_parts[
                        "nucleus"
                    ]

                    hyp_coda = hyp_parts[
                        "coda"
                    ]

                    hyp_tone = hyp_parts[
                        "tone"
                    ]

                else:

                    hyp_initial = ""
                    hyp_medial = ""
                    hyp_nucleus = ""
                    hyp_coda = ""
                    hyp_tone = ""


                # ------------------------------------------
                # Luu ket qua
                # ------------------------------------------

                results.append({

                    "audio":
                        audio,

                    "ground_truth":
                        ground_truth,

                    "prediction":
                        prediction,

                    "reference_word":
                        ref_word,

                    "hypothesis_word":
                        hyp_word,

                    "error_type":
                        error_type,

                    "changed_components":
                        ",".join(
                            analysis.get(
                                "changed_components",
                                []
                            )
                        ),

                    "reference_valid":
                        analysis.get(
                            "reference_valid",
                            ""
                        ),

                    "hypothesis_valid":
                        analysis.get(
                            "hypothesis_valid",
                            ""
                        ),

                    "reference_validation_reason":
                        analysis.get(
                            "reference_validation_reason",
                            ""
                        ),

                    "hypothesis_validation_reason":
                        analysis.get(
                            "hypothesis_validation_reason",
                            ""
                        ),

                    "ref_initial":
                        ref_initial,

                    "hyp_initial":
                        hyp_initial,

                    "ref_medial":
                        ref_medial,

                    "hyp_medial":
                        hyp_medial,

                    "ref_nucleus":
                        ref_nucleus,

                    "hyp_nucleus":
                        hyp_nucleus,

                    "ref_coda":
                        ref_coda,

                    "hyp_coda":
                        hyp_coda,

                    "ref_tone":
                        ref_tone,

                    "hyp_tone":
                        hyp_tone
                })


        # ==================================================
        # Truong hop alignment phuc tap
        # ==================================================

        else:

            results.append({

                "audio":
                    audio,

                "ground_truth":
                    ground_truth,

                "prediction":
                    prediction,

                "reference_word":
                    " ".join(
                        ref_words
                    ),

                "hypothesis_word":
                    " ".join(
                        hyp_words
                    ),

                "error_type":
                    "complex_alignment",

                "changed_components":
                    "",

                "reference_valid":
                    "",

                "hypothesis_valid":
                    "",

                "reference_validation_reason":
                    "",

                "hypothesis_validation_reason":
                    "",

                "ref_initial":
                    "",

                "hyp_initial":
                    "",

                "ref_medial":
                    "",

                "hyp_medial":
                    "",

                "ref_nucleus":
                    "",

                "hyp_nucleus":
                    "",

                "ref_coda":
                    "",

                "hyp_coda":
                    "",

                "ref_tone":
                    "",

                "hyp_tone":
                    ""
            })


# ==========================================================
# Tao DataFrame ket qua
# ==========================================================

result_df = pd.DataFrame(
    results
)


# ==========================================================
# Luu CSV
# ==========================================================

result_df.to_csv(
    output_file,
    index=False,
    encoding="utf-8-sig"
)


# ==========================================================
# Thong ke ket qua
# ==========================================================

print(
    "===== VIETNAMESE ERROR ANALYSIS V3 ====="
)


print(
    "\nTone error:",
    error_counts[
        "tone_error"
    ]
)

print(
    "Initial consonant error:",
    error_counts[
        "initial_consonant_error"
    ]
)

print(
    "Medial error:",
    error_counts[
        "medial_error"
    ]
)

print(
    "Nucleus error:",
    error_counts[
        "nucleus_error"
    ]
)

print(
    "Final consonant error:",
    error_counts[
        "final_consonant_error"
    ]
)

print(
    "Multi-component error:",
    error_counts[
        "multi_component_error"
    ]
)

print(
    "Non-Vietnamese token:",
    error_counts[
        "non_vietnamese_token"
    ]
)

print(
    "Invalid reference token:",
    error_counts[
        "invalid_reference_token"
    ]
)

print(
    "Unknown:",
    error_counts[
        "unknown"
    ]
)


classified_total = sum(
    error_counts.values()
)


complex_alignment_total = len(
    result_df[
        result_df[
            "error_type"
        ]
        == "complex_alignment"
    ]
)


print(
    "\nTong substitution da phan loai:",
    classified_total
)

print(
    "Complex alignment:",
    complex_alignment_total
)

print(
    "Tong dong substitution:",
    len(
        result_df
    )
)


print(
    "\nDa luu:"
)

print(
    output_file
)