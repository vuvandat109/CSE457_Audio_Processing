import os
import pandas as pd
import whisper
from jiwer import wer, cer
from text_normalizer import normalize_vietnamese_text

# ===== DUONG DAN =====
metadata_file = r"E:\ASR_Project\dataset\metadata.csv"
audio_folder = r"E:\ASR_Project\dataset\audio"

output_file = r"E:\ASR_Project\dataset\asr_results.csv"

# ===== THEM FFMPEG VAO PATH =====
os.environ["PATH"] += os.pathsep + r"E:\ffmpeg-2026-09-07-git-ecc7eb519e-essentials_build\bin"

# ===== LOAD DATA =====
df = pd.read_csv(metadata_file, encoding="utf-8-sig")

# TEST 20 FILE TRUOC
df = df.head(20)

print("So file se test:", len(df))

# ===== LOAD WHISPER =====
print("Dang load Whisper...")
model = whisper.load_model("base")

results = []

for index, row in df.iterrows():

    audio_name = row["audio"]
    ground_truth = str(row["text"])

    audio_path = os.path.join(audio_folder, audio_name)

    print(f"\n[{index + 1}/{len(df)}]")
    print("Audio:", audio_name)

    try:
        result = model.transcribe(
            audio_path,
            language="vi",
            fp16=False
        )

        prediction = result["text"].strip()

        # Normalize
        gt_norm = normalize_vietnamese_text(ground_truth)
        pred_norm = normalize_vietnamese_text(prediction)

        # Metrics
        current_wer = wer(gt_norm, pred_norm)
        current_cer = cer(gt_norm, pred_norm)

        print("GT :", ground_truth)
        print("ASR:", prediction)
        print("WER:", round(current_wer, 4))
        print("CER:", round(current_cer, 4))

        results.append({
            "audio": audio_name,
            "ground_truth": ground_truth,
            "prediction": prediction,
            "wer": current_wer,
            "cer": current_cer
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


# ===== SAVE =====
result_df = pd.DataFrame(results)

result_df.to_csv(
    output_file,
    index=False,
    encoding="utf-8-sig"
)

print("\n==============================")
print("HOAN TAT")
print("Da luu ket qua tai:")
print(output_file)

if len(result_df) > 0:
    print("\nWER trung binh:", result_df["wer"].mean())
    print("CER trung binh:", result_df["cer"].mean())