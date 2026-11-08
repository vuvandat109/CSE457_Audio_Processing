"""Optional offline Whisper inference; the dashboard reads saved results."""
import os
import shutil
from pathlib import Path

_model = None

def transcribe_audio(audio_path):
    global _model
    audio_path = Path(audio_path)
    if not audio_path.is_file():
        raise FileNotFoundError(audio_path)
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("FFmpeg is not on PATH")
    if _model is None:
        import whisper
        _model = whisper.load_model(os.getenv("WHISPER_MODEL", "base"))
    result = _model.transcribe(str(audio_path), language="vi", fp16=False,
                               temperature=0, condition_on_previous_text=False)
    return result["text"].strip()
