import os

# Them FFmpeg vao PATH cho Python
os.environ["PATH"] += os.pathsep + r"E:\ffmpeg-2026-09-07-git-ecc7eb519e-essentials_build\bin"

import whisper

print("Dang tai model Whisper...")

model = whisper.load_model("base")

audio_folder = r"E:\ASR_Project\dataset\audio"

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