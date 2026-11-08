"""Smoke-test all three ASR engines on an actual Common Voice MP3.

Run from Vietnamese-ASR-Analyzer:
    python code/smoke_test_three_models.py
Requires: pip install -r requirements-asr.txt
FFmpeg and model downloads/checkpoints must be available.
Outputs dataset/smoke_test_three_models.json for inspection.
"""
import csv
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "web" / "backend"))
from asr_runtime import transcribe_audio

MODELS = ("whisper", "phowhisper", "wav2vec2")


def main():
    metadata_path = ROOT / "dataset" / "metadata.csv"
    with metadata_path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise RuntimeError("metadata.csv contains no audio rows")
    row = next(
        (r for r in rows if (ROOT / "dataset" / "audio" / r["audio"]).is_file()),
        None,
    )
    if row is None:
        raise RuntimeError("No MP3 listed in metadata.csv is present in dataset/audio")
    audio = ROOT / "dataset" / "audio" / row["audio"]
    report = {"audio": audio.name, "reference": row.get("text", ""), "models": {}}
    for model in MODELS:
        start = time.perf_counter()
        try:
            prediction = transcribe_audio(audio, model)
            from audio_analyzer import calculate_score
            metrics = calculate_score(row.get("text", ""), prediction)
            result = {
                "status": "success",
                "prediction": prediction,
                "wer": metrics["wer"],
                "cer": metrics["cer"],
            }
        except Exception as exc:
            result = {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}
        result["seconds"] = round(time.perf_counter() - start, 2)
        report["models"][model] = result
        print(f"{model}: {result}", flush=True)
    output = ROOT / "dataset" / "smoke_test_three_models.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved: {output}")
    return 0 if all(x["status"] == "success" for x in report["models"].values()) else 1


if __name__ == "__main__":
    sys.exit(main())
