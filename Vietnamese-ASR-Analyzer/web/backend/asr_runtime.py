# -*- coding: utf-8 -*-

"""
asr_runtime.py

Nhan dang 1 file audio moi bang 3 model:
- Whisper base
- PhoWhisper base
- Wav2Vec2 Vietnamese

Model duoc lazy-load: chi load khi nguoi dung thuc su chon model do.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from threading import Lock

# Phai dat truoc khi import transformers
os.environ.setdefault(
    "DISABLE_SAFETENSORS_CONVERSION",
    "1"
)

import librosa
import numpy as np
import torch


WHISPER_MODEL_NAME = "base"
PHOWHISPER_MODEL_ID = "vinai/PhoWhisper-base"
WAV2VEC2_MODEL_ID = "khanhld/wav2vec2-base-vietnamese-160h"
TARGET_SAMPLE_RATE = 16000


# FFMPEG: uu tien PATH he thong, neu khong co thi thu duong dan user dang dung
KNOWN_FFMPEG_DIRS = [
    Path(
        r"E:\ffmpeg-2026-09-07-git-ecc7eb519e-essentials_build\bin"
    )
]

if shutil.which("ffmpeg") is None:
    for folder in KNOWN_FFMPEG_DIRS:
        if folder.exists():
            os.environ["PATH"] = (
                str(folder)
                + os.pathsep
                + os.environ.get("PATH", "")
            )
            break


_model_cache = {}
_model_lock = Lock()


def _device():
    return torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )


def _load_whisper():
    import whisper

    return whisper.load_model(
        WHISPER_MODEL_NAME
    )


def _load_phowhisper():
    from transformers import pipeline

    device_index = (
        0
        if torch.cuda.is_available()
        else -1
    )

    return pipeline(
        task="automatic-speech-recognition",
        model=PHOWHISPER_MODEL_ID,
        device=device_index
    )


def _load_wav2vec2():
    from transformers import (
        AutoProcessor,
        AutoModelForCTC
    )

    processor = AutoProcessor.from_pretrained(
        WAV2VEC2_MODEL_ID
    )

    model = AutoModelForCTC.from_pretrained(
        WAV2VEC2_MODEL_ID,
        use_safetensors=False
    )

    device = _device()

    model.to(
        device
    )

    model.eval()

    return {
        "processor": processor,
        "model": model,
        "device": device
    }


def get_model(model_key: str):

    if model_key in _model_cache:
        return _model_cache[model_key]

    with _model_lock:

        if model_key in _model_cache:
            return _model_cache[model_key]

        print(
            f"[ASR] Loading model: {model_key}"
        )

        if model_key == "whisper":
            loaded = _load_whisper()

        elif model_key == "phowhisper":
            loaded = _load_phowhisper()

        elif model_key == "wav2vec2":
            loaded = _load_wav2vec2()

        else:
            raise ValueError(
                f"Unsupported model: {model_key}"
            )

        _model_cache[model_key] = loaded

        print(
            f"[ASR] Model ready: {model_key}"
        )

        return loaded


def transcribe_whisper(audio_path: Path) -> str:

    model = get_model(
        "whisper"
    )

    result = model.transcribe(
        str(audio_path),
        language="vi",
        fp16=False,
        temperature=0,
        condition_on_previous_text=False
    )

    return str(
        result.get(
            "text",
            ""
        )
    ).strip()


def transcribe_phowhisper(audio_path: Path) -> str:

    asr = get_model(
        "phowhisper"
    )

    output = asr(
        str(audio_path),
        generate_kwargs={
            "language": "vi",
            "task": "transcribe"
        }
    )

    if isinstance(
        output,
        dict
    ):
        return str(
            output.get(
                "text",
                ""
            )
        ).strip()

    return str(
        output
    ).strip()


def convert_to_wav_16k_mono(audio_path: Path) -> Path:
    """
    Chuyen audio upload (webm/ogg/mp3/m4a/...) sang WAV PCM 16 kHz mono.
    Wav2Vec2/librosa tren Windows co the khong doc truc tiep WebM tu MediaRecorder.
    """

    ffmpeg = shutil.which("ffmpeg")

    if not ffmpeg:
        raise RuntimeError(
            "Khong tim thay ffmpeg. Hay cai FFmpeg hoac them ffmpeg vao PATH."
        )

    fd, output_name = tempfile.mkstemp(
        suffix=".wav"
    )
    os.close(fd)

    output_path = Path(output_name)

    command = [
        ffmpeg,
        "-y",
        "-loglevel",
        "error",
        "-i",
        str(audio_path),
        "-ac",
        "1",
        "-ar",
        str(TARGET_SAMPLE_RATE),
        "-c:a",
        "pcm_s16le",
        str(output_path),
    ]

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False
        )

        if completed.returncode != 0:
            raise RuntimeError(
                "FFmpeg khong the chuyen doi audio: "
                + (completed.stderr.strip() or "unknown error")
            )

        if (
            not output_path.exists()
            or output_path.stat().st_size == 0
        ):
            raise RuntimeError(
                "FFmpeg tao file WAV rong."
            )

        return output_path

    except Exception:
        try:
            output_path.unlink(
                missing_ok=True
            )
        except OSError:
            pass

        raise


def transcribe_wav2vec2(audio_path: Path) -> str:

    bundle = get_model(
        "wav2vec2"
    )

    converted_path = None

    try:
        # Browser MediaRecorder thuong tao WebM/Opus.
        # Chuyen qua WAV PCM de tranh loi "Format not recognised".
        converted_path = convert_to_wav_16k_mono(
            audio_path
        )

        waveform, _ = librosa.load(
            str(converted_path),
            sr=TARGET_SAMPLE_RATE,
            mono=True
        )

        waveform = np.asarray(
            waveform,
            dtype=np.float32
        )

        inputs = bundle[
            "processor"
        ](
            waveform,
            sampling_rate=TARGET_SAMPLE_RATE,
            return_tensors="pt",
            padding=True
        )

        input_values = inputs.input_values.to(
            bundle["device"]
        )

        attention_mask = getattr(
            inputs,
            "attention_mask",
            None
        )

        if attention_mask is not None:
            attention_mask = attention_mask.to(
                bundle["device"]
            )

        with torch.inference_mode():

            outputs = bundle[
                "model"
            ](
                input_values,
                attention_mask=attention_mask
            )

        predicted_ids = torch.argmax(
            outputs.logits,
            dim=-1
        )

        prediction = bundle[
            "processor"
        ].batch_decode(
            predicted_ids
        )[0]

        return str(
            prediction
        ).strip()

    finally:
        if converted_path is not None:
            try:
                converted_path.unlink(
                    missing_ok=True
                )
            except OSError:
                pass


def transcribe_audio(
    audio_path: Path,
    model_key: str
) -> str:

    if model_key == "whisper":
        return transcribe_whisper(
            audio_path
        )

    if model_key == "phowhisper":
        return transcribe_phowhisper(
            audio_path
        )

    if model_key == "wav2vec2":
        return transcribe_wav2vec2(
            audio_path
        )

    raise ValueError(
        f"Unsupported model: {model_key}"
    )


def loaded_models():

    return sorted(
        _model_cache.keys()
    )
