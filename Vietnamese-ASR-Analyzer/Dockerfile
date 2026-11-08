# syntax=docker/dockerfile:1
# One public service: Vite/React static build + Python/FastAPI + Wav2Vec2 ASR engine.
FROM node:22-bookworm-slim AS frontend
WORKDIR /frontend
COPY web/frontend/package*.json ./
RUN npm ci
COPY web/frontend/ ./
RUN npm run build

FROM python:3.11-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    USE_TF=0 \
    USE_FLAX=0 \
    OMP_NUM_THREADS=2 \
    TOKENIZERS_PARALLELISM=false \
    ASR_FRONTEND_DIST=/app/web/frontend/dist \
    PORT=10000
RUN apt-get update && apt-get install -y --no-install-recommends \
      ffmpeg libsndfile1 libgomp1 ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
# The matching CPU-only PyTorch wheels avoid pulling multi-GB CUDA dependencies.
RUN python -m pip install --upgrade pip && \
    python -m pip install --index-url https://download.pytorch.org/whl/cpu \
      torch==2.5.1
COPY web/backend/requirements.docker.txt /tmp/requirements.docker.txt
RUN python -m pip install -r /tmp/requirements.docker.txt
RUN useradd --create-home --uid 10001 asr
COPY --chown=asr:asr . /app/
COPY --from=frontend --chown=asr:asr /frontend/dist /app/web/frontend/dist
USER asr
ENV HOME=/home/asr \
    HF_HOME=/home/asr/.cache/huggingface \
    XDG_CACHE_HOME=/home/asr/.cache
WORKDIR /app/web/backend
EXPOSE 10000
HEALTHCHECK --interval=45s --timeout=15s --start-period=90s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:10000/health',timeout=10)"
CMD ["sh", "-c", "exec python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000} --workers 1"]
