import os
import pandas as pd
import whisper

from jiwer import wer, cer
from text_normalizer import normalize_vietnamese_text


# =====================================================
# DUONG DAN
# =====================================================

metadata_file = r"E:\ASR_Project\dataset\metadata.csv"
audio_folder = r"E:\ASR_Project\dataset\audio"

# TEST RIENG - KHONG GHI DE FILE 1000 MAU
output_file = r"E:\ASR_Project\dataset\asr_results_new.csv"

# =====================================================
# FFMPEG
# =====================================================

os.environ["PATH"] += (
    os.pathsep
    + r"E:\ffmpeg-2026-09-07-git-ecc7eb519e-essentials_build\bin"
)


# =====================================================
# LOAD DATA
# =====================================================

df = pd.read_csv(
    metadata_file,
    encoding="utf-8-sig"
)


# =====================================================
# TEST 20 MAU TRUOC
# =====================================================

TEST_LIMIT = 1000

df = df.head(TEST_LIMIT)

print("==============================")
print("So file se test:", len(df))
print("==============================")


# =====================================================
# LOAD WHISPER
# =====================================================

print("Dang load Whisper...")
model = whisper.load_model("base")
print("Da load Whisper.")


# =====================================================
# RESULTS
# =====================================================

results = []


# =====================================================
# CHAY TUNG AUDIO
# =====================================================

for index, row in df.iterrows():

    audio_name = str(row["audio"]).strip()
    ground_truth = str(row["text"]).strip()
    audio_path = os.path.join(audio_folder, audio_name)

    print("\n==============================")
    print(f"[{index + 1}/{len(df)}]")
    print("Audio:", audio_name)
    print("Path:", audio_path)

    # =================================================
    # KIEM TRA FILE AUDIO
    # =================================================

    if not os.path.exists(audio_path):

        error_message = f"Khong tim thay audio: {audio_path}"

        print("LOI:", error_message)

        results.append({
            "audio": audio_name,
            "ground_truth": ground_truth,
            "prediction": "",
            "wer": "",
            "cer": "",
            "error": error_message
        })

        continue

    try:

        # =============================================
        # WHISPER TRANSCRIBE
        # =============================================

        result = model.transcribe(
            audio_path,
            language="vi",
            fp16=False,
            temperature=0,
            condition_on_previous_text=False
        )

        prediction = str(
            result.get("text", "")
        ).strip()

        # =============================================
        # NORMALIZE
        # =============================================

        gt_norm = normalize_vietnamese_text(
            ground_truth
        )

        pred_norm = normalize_vietnamese_text(
            prediction
        )

        # =============================================
        # METRICS
        # =============================================

        current_wer = wer(
            gt_norm,
            pred_norm
        )

        current_cer = cer(
            gt_norm,
            pred_norm
        )

        # =============================================
        # PRINT
        # =============================================

        print("GT :", ground_truth)
        print("ASR:", prediction)
        print("GT Normalize :", gt_norm)
        print("ASR Normalize:", pred_norm)
        print("WER:", round(current_wer, 4))
        print("CER:", round(current_cer, 4))

        # =============================================
        # SAVE RESULT
        # =============================================

        results.append({
            "audio": audio_name,
            "ground_truth": ground_truth,
            "prediction": prediction,
            "wer": current_wer,
            "cer": current_cer,
            "error": ""
        })

    except Exception as e:

        print("LOI:", e)

        results.append({
            "audio": audio_name,
            "ground_truth": ground_truth,
            "prediction": "",
            "wer": "",
            "cer": "",
            "error": str(e)
        })


# =====================================================
# SAVE CSV
# =====================================================

result_df = pd.DataFrame(results)

result_df.to_csv(
    output_file,
    index=False,
    encoding="utf-8-sig"
)


# =====================================================
# SUMMARY
# =====================================================

print("\n==============================")
print("HOAN TAT")
print("==============================")

print("Tong mau:", len(result_df))

success_df = result_df[
    result_df["wer"] != ""
].copy()

if len(success_df) > 0:

    success_df["wer"] = pd.to_numeric(
        success_df["wer"],
        errors="coerce"
    )

    success_df["cer"] = pd.to_numeric(
        success_df["cer"],
        errors="coerce"
    )

    print(
        "WER trung binh:",
        success_df["wer"].mean()
    )

    print(
        "CER trung binh:",
        success_df["cer"].mean()
    )

print("Da luu ket qua tai:")
print(output_file)
print("==============================")
