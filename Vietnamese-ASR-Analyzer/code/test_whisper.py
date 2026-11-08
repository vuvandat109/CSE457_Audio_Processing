from pathlib import Path
DATASET_DIR = Path(__file__).resolve().parents[1] / "dataset"

import os
import shutil

if shutil.which("ffmpeg") is None:
    raise SystemExit("Install FFmpeg and add it to PATH")

import whisper

print("Dang tai model Whisper...")

model = whisper.load_model(os.getenv("WHISPER_MODEL", "base"))

audio_folder = str(DATASET_DIR / "audio")

files = [
    f for f in os.listdir(audio_folder)
    if f.lower().endswith(".mp3")
]

if not files:
    print("LOI: Khong tim thay file MP3")
    exit()

audio_file = os.path.join(audio_folder, files[0])

print("File dang test:")
print(audio_file)

print("\nDang nhan dang tieng Viet...")

result = model.transcribe(
    audio_file,
    language="vi"
)

print("\n===== KET QUA WHISPER =====")
print(result["text"])
