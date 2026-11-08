# -*- coding: utf-8 -*-

import json
import os
import tempfile
import time
import uuid

from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form, Request
from starlette.concurrency import run_in_threadpool
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware


from audio_analyzer import (
    word_alignment,
    simple_error_check,
    analyze_sentence_phoneme,
    calculate_score
)

from asr_runtime import (
    transcribe_audio,
    loaded_models
)


# =====================================================
# CONFIG
# =====================================================

API_VERSION = "1.0.0"
API_PREFIX = "/api/v1"
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "50"))
if MAX_UPLOAD_MB <= 0:
    raise ValueError("MAX_UPLOAD_MB phải lớn hơn 0")
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

BASE_DIR = Path(
    os.getenv(
        "ASR_DATASET_DIR",
        Path(__file__).resolve().parents[2] / "dataset"
    )
)

STAT_FILES = {
    "whisper": BASE_DIR / "error_statistics_whisper.json",
    "phowhisper": BASE_DIR / "error_statistics_phowhisper.json",
    "wav2vec2": BASE_DIR / "error_statistics_wav2vec2.json",
}
MODEL_COMPARISON_FILE = BASE_DIR / "model_comparison.json"

ANALYSIS_FILES = {
    "whisper": BASE_DIR / "sentence_analysis_whisper.json",
    "phowhisper": BASE_DIR / "sentence_analysis_phowhisper.json",
    "wav2vec2": BASE_DIR / "sentence_analysis_wav2vec2.json",
}

MODEL_NAMES = {
    "whisper": "Whisper base",
    "phowhisper": "PhoWhisper base",
    "wav2vec2": "Wav2Vec2 Vietnamese",
}

DEFAULT_MODEL = "whisper"

ALLOWED_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,http://localhost:3000"
).split(",")
ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS if origin.strip()]


STATUS_MAP = {
    "correct": "correct",
    "Đúng": "correct",

    "incorrect": "incorrect",
    "Sai": "incorrect",

    "failed": "failed",
    "Lỗi phân tích": "failed"
}


# =====================================================
# APP
# =====================================================

app = FastAPI(
    title="Vietnamese ASR Error Analyzer API",
    version=API_VERSION,
    description="API nhận dạng và phân tích lỗi tiếng Việt với ba mô hình ASR."
)


# =====================================================
# AUDIO STATIC FILE
# =====================================================

AUDIO_DIR = BASE_DIR / "audio"

app.mount(
    "/audio",
    StaticFiles(directory=AUDIO_DIR, check_dir=False),
    name="audio"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# =====================================================
# CACHE
# =====================================================

_json_cache: dict[Path, tuple[float, Any]] = {}

_indexes = {
    "whisper": {
        "src": None,
        "items": [],
        "by_audio": {}
    },
    "phowhisper": {
        "src": None,
        "items": [],
        "by_audio": {}
    },
    "wav2vec2": {
        "src": None,
        "items": [],
        "by_audio": {}
    }
}


# =====================================================
# LOAD JSON
# =====================================================

def load_json(path: Path):

    try:
        mtime = path.stat().st_mtime

    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail=f"Chưa có file {path.name}"
        )

    cached = _json_cache.get(path)

    if cached and cached[0] == mtime:
        return cached[1]

    try:
        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:
            data = json.load(f)

    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi JSON {path.name}: {e}"
        )

    _json_cache[path] = (
        mtime,
        data
    )

    return data


# =====================================================
# MODEL VALIDATION
# =====================================================

def normalize_model(model: Optional[str]) -> str:

    model = (
        str(model).strip().lower()
        if model is not None
        else DEFAULT_MODEL
    )

    if model not in ANALYSIS_FILES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Model không hợp lệ: {model}. "
                f"Hỗ trợ: {', '.join(ANALYSIS_FILES.keys())}"
            )
        )

    return model


# =====================================================
# INDEX AUDIO BY MODEL
# =====================================================

def get_items(model: str = DEFAULT_MODEL):

    model = normalize_model(model)

    analysis_file = ANALYSIS_FILES[model]
    data = load_json(analysis_file)

    index = _indexes[model]

    if index["src"] is not data:

        items = data.get(
            "data",
            []
        )

        for item in items:

            item["status"] = STATUS_MAP.get(
                item.get("status"),
                "failed"
            )

            item["model"] = item.get(
                "model",
                model
            )

            item["model_name"] = item.get(
                "model_name",
                MODEL_NAMES[model]
            )

        index.update({
            "src": data,
            "items": items,
            "by_audio": {
                x.get("audio"): x
                for x in items
            }
        })

    return (
        index["items"],
        index["by_audio"]
    )


# =====================================================
# NUMBER CONVERT
# =====================================================

def _num(value) -> Optional[float]:

    try:
        return float(value)

    except (TypeError, ValueError):
        return None


# =====================================================
# HOME
# =====================================================

@app.get("/")
def home():

    return {
        "message": "Vietnamese ASR Error Analyzer API",
        "models": [
            {
                "key": key,
                "name": MODEL_NAMES[key]
            }
            for key in ANALYSIS_FILES
        ],
        "default_model": DEFAULT_MODEL
    }


# =====================================================
# MODELS
# =====================================================

@app.get("/api/models")
@app.get("/api/v1/models", tags=["Models"])
def models():

    return {
        "default": DEFAULT_MODEL,
        "models": [
            {
                "key": key,
                "name": MODEL_NAMES[key]
            }
            for key in ANALYSIS_FILES
        ]
    }


# =====================================================
# STATISTICS
# =====================================================

@app.get("/api/statistics")
@app.get("/api/v1/analytics/statistics", tags=["Analytics"])
def statistics(
    model: str = Query(
        DEFAULT_MODEL,
        pattern="^(whisper|phowhisper|wav2vec2)$"
    )
):

    model = normalize_model(model)

    stat = dict(
        load_json(
            STAT_FILES[model]
        )
    )

    return stat


# =====================================================
# MODEL COMPARISON
# =====================================================

@app.get("/api/model-comparison")
@app.get("/api/v1/analytics/model-comparison", tags=["Analytics"])
def model_comparison():

    data = load_json(
        MODEL_COMPARISON_FILE
    )

    models = data.get(
        "models",
        []
    )

    best = data.get(
        "best",
        {}
    )

    return {
        "models": models,
        "best": best,
        "total_models": len(models)
    }



# =====================================================
# TEST NEW AUDIO
# =====================================================

@app.post("/api/test-audio")
@app.post("/api/v1/asr/transcribe", tags=["ASR"])
async def test_audio(
    file: UploadFile = File(...),
    model: str = Form(DEFAULT_MODEL),
    ground_truth: str = Form("")
):

    model = normalize_model(
        model
    )

    filename = (
        file.filename
        or "uploaded_audio.wav"
    )

    suffix = Path(
        filename
    ).suffix.lower()

    allowed_suffixes = {
        ".wav",
        ".mp3",
        ".m4a",
        ".flac",
        ".ogg",
        ".webm",
        ".aac"
    }

    if suffix not in allowed_suffixes:

        raise HTTPException(
            status_code=400,
            detail=(
                "Định dạng audio không hỗ trợ. "
                "Hỗ trợ: WAV, MP3, M4A, FLAC, OGG, WEBM, AAC."
            )
        )

    content = await file.read(MAX_UPLOAD_BYTES + 1)

    if not content:

        raise HTTPException(
            status_code=400,
            detail="File audio rỗng."
        )

    max_size = MAX_UPLOAD_BYTES

    if len(content) > max_size:

        raise HTTPException(
            status_code=413,
            detail=f"File audio vượt quá {MAX_UPLOAD_MB} MB."
        )

    temp_path = None

    try:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as tmp:

            tmp.write(
                content
            )

            temp_path = Path(
                tmp.name
            )

        started = time.perf_counter()

        prediction = await run_in_threadpool(
            transcribe_audio,
            temp_path,
            model
        )

        processing_seconds = (
            time.perf_counter()
            - started
        )

        reference = str(
            ground_truth
            or ""
        ).strip()

        response = {
            "audio": filename,
            "model": model,
            "model_name": MODEL_NAMES[model],
            "prediction": prediction,
            "ground_truth": reference,
            "processing_seconds": round(
                processing_seconds,
                3
            ),
            "loaded_models": loaded_models(),
            "has_ground_truth": bool(
                reference
            ),
            "wer": None,
            "cer": None,
            "status": "unscored",
            "errors": [],
            "alignment": [],
            "word_analysis": []
        }

        if reference:

            alignment = word_alignment(
                reference,
                prediction
            )

            errors = simple_error_check(
                alignment
            )

            word_analysis = analyze_sentence_phoneme(
                alignment
            )

            score = calculate_score(
                reference,
                prediction
            )

            response.update({
                "wer": score.get(
                    "wer"
                ),
                "cer": score.get(
                    "cer"
                ),
                "status": (
                    "correct"
                    if len(errors) == 0
                    else "incorrect"
                ),
                "errors": errors,
                "alignment": alignment,
                "word_analysis": word_analysis
            })

        return response

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Không thể nhận dạng audio bằng "
                f"{MODEL_NAMES[model]}: {exc}"
            )
        )

    finally:

        if (
            temp_path is not None
            and temp_path.exists()
        ):

            try:
                temp_path.unlink()
            except OSError:
                pass


# =====================================================
# AUDIO LIST
# =====================================================

@app.get("/api/audio-list")
@app.get("/api/v1/analytics/audio-list", tags=["Analytics"])
def audio_list(
    model: str = Query(
        DEFAULT_MODEL,
        pattern="^(whisper|phowhisper|wav2vec2)$"
    ),

    status: Optional[str] = Query(
        None,
        pattern="^(correct|incorrect|failed)$"
    ),

    q: Optional[str] = None,

    limit: Optional[int] = Query(
        None,
        ge=1,
        le=5000
    ),

    offset: int = Query(
        0,
        ge=0
    )
):

    model = normalize_model(model)

    items, _ = get_items(model)

    if status:
        items = [
            x
            for x in items
            if x["status"] == status
        ]

    if q:
        q = q.lower()

        items = [
            x
            for x in items
            if q in str(
                x.get("audio", "")
            ).lower()
        ]

    total = len(items)

    page = (
        items[offset:offset + limit]
        if limit
        else items[offset:]
    )

    return {
        "model": model,
        "model_name": MODEL_NAMES[model],
        "total": total,
        "data": [
            {
                "audio": x.get("audio"),
                "wer": x.get("wer"),
                "cer": x.get("cer"),
                "status": x["status"],
                "errors": x.get(
                    "errors",
                    []
                ),
                "model": model,
                "model_name": MODEL_NAMES[model]
            }
            for x in page
        ]
    }


# =====================================================
# AUDIO DETAIL
# =====================================================

@app.get("/api/audio-detail/{audio:path}")
@app.get("/api/v1/analytics/audio-detail/{audio:path}", tags=["Analytics"])
def audio_detail(
    audio: str,
    model: str = Query(
        DEFAULT_MODEL,
        pattern="^(whisper|phowhisper|wav2vec2)$"
    )
):

    model = normalize_model(model)

    _, by_audio = get_items(model)

    item = by_audio.get(audio)

    if item is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Audio not found in model {model}: {audio}"
            )
        )

    return item


# =====================================================
# SYSTEM / API METADATA
# =====================================================

@app.middleware("http")
async def api_metadata(request: Request, call_next):
    request_id = str(uuid.uuid4())
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-API-Version"] = API_VERSION
    response.headers["X-Process-Time"] = f"{time.perf_counter() - started:.4f}"
    return response


@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "version": API_VERSION}


@app.get("/ready", tags=["System"])
def ready():
    from fastapi.responses import JSONResponse

    checks = {
        "dataset_dir": BASE_DIR.is_dir(),
        "audio_dir": AUDIO_DIR.is_dir(),
        "statistics": {key: path.is_file() for key, path in STAT_FILES.items()},
        "analysis": {key: path.is_file() for key, path in ANALYSIS_FILES.items()},
        "model_comparison": MODEL_COMPARISON_FILE.is_file(),
    }
    ok = (
        checks["dataset_dir"]
        and checks["audio_dir"]
        and all(checks["statistics"].values())
        and all(checks["analysis"].values())
        and checks["model_comparison"]
    )
    return JSONResponse(
        status_code=200 if ok else 503,
        content={"status": "ready" if ok else "degraded", "checks": checks},
    )


@app.get("/api/v1/system/info", tags=["System"])
def system_info():
    return {
        "version": API_VERSION,
        "api_prefix": API_PREFIX,
        "max_upload_mb": MAX_UPLOAD_MB,
        "loaded_models": loaded_models(),
        "supported_audio": [".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm", ".aac"],
    }
