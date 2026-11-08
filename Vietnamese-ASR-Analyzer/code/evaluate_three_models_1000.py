# -*- coding: utf-8 -*-
"""Run all three pretrained ASR models on the same metadata MP3s.

Safe by default: writes dataset/evaluation_recheck/, never overwrites dashboard CSVs.
Resume is supported through an append-only CSV per model, including failures.
Examples:
  python code/evaluate_three_models_1000.py --limit 5
  python code/evaluate_three_models_1000.py --limit 1000
  python code/evaluate_three_models_1000.py --limit 1000 --models wav2vec2
"""
import argparse
import csv
import hashlib
import json
import math
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "web" / "backend"))
MODELS = ("whisper", "phowhisper", "wav2vec2")
FIELDS = ("audio", "ground_truth", "prediction", "wer", "cer", "status", "error", "seconds")
OUTPUT_DIR = ROOT / "dataset" / "evaluation_recheck"


def load_metadata(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or not {"audio", "text"}.issubset(rows[0]):
        raise ValueError("metadata must contain audio and text columns")
    names = [row["audio"] for row in rows]
    if any(not name or Path(name).name != name or "/" in name or chr(92) in name for name in names):
        raise ValueError("metadata contains invalid/non-local audio names")
    if len(names) != len(set(names)):
        raise ValueError("Duplicate audio names in metadata")
    return rows


def load_previous(path, metadata):
    if not path.exists():
        return {}
    allowed = {row["audio"]: row["text"] for row in metadata}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(FIELDS):
            raise ValueError(f"Unexpected result columns: {path}")
        rows = list(reader)
    previous = {}
    for row in rows:
        name = row["audio"]
        if name not in allowed or row["ground_truth"] != allowed[name] or name in previous:
            raise ValueError(f"Results do not match metadata or duplicate audio: {name}")
        previous[name] = row
    return previous


def score(reference, prediction):
    from audio_analyzer import calculate_score
    return calculate_score(reference, prediction)


def append_result(path, result):
    new_file = not path.exists()
    with path.open("a", newline="", encoding="utf-8-sig" if new_file else "utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow(result)
        handle.flush()
        os.fsync(handle.fileno())


def summarize(path, expected, model):
    previous = load_previous(path, expected)
    completed = [row for row in previous.values() if row["status"] == "ok"]
    failed = [row for row in previous.values() if row["status"] == "failed"]
    mean = lambda field: (sum(float(row[field]) for row in completed) / len(completed)) if completed else None
    return {
        "model": model,
        "expected_samples": len(expected),
        "recorded_samples": len(previous),
        "successful_samples": len(completed),
        "failed_samples": len(failed),
        "remaining_samples": len(expected) - len(previous),
        "exact_matches": sum(float(row["wer"]) == 0 and float(row["cer"]) == 0 for row in completed),
        "mean_wer_successful_only": mean("wer"),
        "mean_cer_successful_only": mean("cer"),
        "complete": len(previous) == len(expected) and len(failed) == 0,
        "failed_audio": [row["audio"] for row in failed],
        "result_file": path.name,
    }


def main(argv=None, transcribe=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=5, help="Number of metadata rows (default: 5; full: 1000)")
    parser.add_argument("--models", nargs="+", choices=MODELS, default=list(MODELS))
    parser.add_argument("--retry-failed", action="store_true", help="Retry failures by rewriting a validated CSV")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args(argv)
    metadata_file = ROOT / "dataset" / "metadata.csv"
    metadata_all = load_metadata(metadata_file)
    if args.limit < 1 or args.limit > len(metadata_all):
        parser.error(f"--limit must be from 1 to {len(metadata_all)}")
    chosen = metadata_all[:args.limit]
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    fingerprint = hashlib.sha256(metadata_file.read_bytes()).hexdigest()
    manifest = output / "manifest.json"
    expected_info = {"metadata_sha256": fingerprint, "limit": args.limit,
                     "audio_names": [r["audio"] for r in chosen]}
    if manifest.exists():
        existing = json.loads(manifest.read_text(encoding="utf-8"))
        if any(existing.get(k) != v for k, v in expected_info.items()):
            raise ValueError("Existing evaluation directory uses a different metadata or --limit. Use another --output-dir.")
    else:
        if any(output.glob("results_*.csv")):
            raise ValueError("Result CSV exists without manifest; use a fresh output folder")
        manifest.write_text(json.dumps(expected_info, ensure_ascii=False, indent=2), encoding="utf-8")
    if transcribe is None:
        from asr_runtime import transcribe_audio
        transcribe = transcribe_audio
    for model in args.models:
        path = output / f"results_{model}.csv"
        previous = load_previous(path, chosen)
        if args.retry_failed and any(x["status"] == "failed" for x in previous.values()):
            keep = [previous[row["audio"]] for row in chosen
                    if row["audio"] in previous and previous[row["audio"]]["status"] == "ok"]
            temp = path.with_suffix(".tmp")
            with temp.open("w", newline="", encoding="utf-8-sig") as handle:
                writer = csv.DictWriter(handle, fieldnames=FIELDS)
                writer.writeheader()
                writer.writerows(keep)
            temp.replace(path)
            previous = load_previous(path, chosen)
        print(f"Model {model}: {len(previous)}/{len(chosen)} already recorded", flush=True)
        for index, item in enumerate(chosen, 1):
            name, reference = item["audio"], item["text"]
            if name in previous:
                continue
            audio = ROOT / "dataset" / "audio" / name
            begin = time.perf_counter()
            result = dict(audio=name, ground_truth=reference, prediction="",
                          wer="", cer="", status="failed", error="", seconds=0)
            try:
                if not audio.is_file():
                    raise FileNotFoundError(str(audio))
                prediction = str(transcribe(audio, model))
                metrics = score(reference, prediction)
                result.update(prediction=prediction, wer=metrics["wer"], cer=metrics["cer"], status="ok")
            except Exception as exc:
                result["error"] = f"{type(exc).__name__}: {exc}"
            result["seconds"] = round(time.perf_counter() - begin, 3)
            append_result(path, result)
            print(f"[{model}] {index}/{len(chosen)} {name}: {result['status']}", flush=True)
        summary = summarize(path, chosen, model)
        (output / f"summary_{model}.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(summary, ensure_ascii=False), flush=True)
    # If there are failures, report them clearly and return nonzero.
    return 0 if all(summarize(output / f"results_{m}.csv", chosen, m)["complete"]
                    for m in args.models) else 1


if __name__ == "__main__":
    sys.exit(main())
