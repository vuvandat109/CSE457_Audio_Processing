import whisper
import os


# ==============================
# SET FFMPEG PATH
# ==============================

FFMPEG_PATH = (
    r"E:\ffmpeg-2026-09-07-git-ecc7eb519e-essentials_build\bin"
)


os.environ["PATH"] += os.pathsep + FFMPEG_PATH



# ==============================
# LOAD MODEL
# ==============================

print("Loading Whisper model...")


model = whisper.load_model("small")


print("Whisper model loaded")




def transcribe_audio(audio_path):


    if not os.path.exists(audio_path):

        raise FileNotFoundError(
            "Audio file not found"
        )


    result = model.transcribe(

        audio_path,

        language="vi",

        task="transcribe",

        fp16=False,

        temperature=0,

        condition_on_previous_text=False,

        initial_prompt="Đây là đoạn hội thoại tiếng Việt."

    )


    print("WHISPER RESULT:")
    print(result)


    return result["text"].strip()