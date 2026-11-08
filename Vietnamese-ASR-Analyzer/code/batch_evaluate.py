"""Run Whisper over a reproducible subset of Common Voice clips."""
import argparse
import os
import shutil
from pathlib import Path
import pandas as pd
from jiwer import cer, wer
from text_normalizer import normalize_vietnamese_text

DATASET_DIR = Path(__file__).resolve().parents[1] / "dataset"

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", type=Path, default=DATASET_DIR / "metadata.csv")
    parser.add_argument("--audio-dir", type=Path, default=DATASET_DIR / "audio")
    parser.add_argument("--output", type=Path, default=DATASET_DIR / "asr_results.csv")
    parser.add_argument("--limit", type=int, default=20, help="0 evaluates all rows")
    parser.add_argument("--sample", action="store_true", help="sample with seed instead of first rows")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--model", default=os.getenv("WHISPER_MODEL", "base"))
    args = parser.parse_args()
    if shutil.which("ffmpeg") is None:
        parser.error("FFmpeg is required. Install it and add its bin directory to PATH.")
    if args.limit < 0:
        parser.error("--limit must be nonnegative")
    df = pd.read_csv(args.metadata, encoding="utf-8-sig")
    if not {"audio", "text"}.issubset(df.columns):
        parser.error("metadata must contain audio,text columns")
    if args.limit:
        df = df.sample(n=min(args.limit, len(df)), random_state=args.seed) if args.sample else df.head(args.limit)
    if df.empty:
        parser.error("No metadata rows selected")
    if not args.audio_dir.is_dir():
        parser.error(f"Audio directory missing: {args.audio_dir}")
    import whisper
    model = whisper.load_model(args.model)
    results = []
    for i, row in enumerate(df.itertuples(index=False), 1):
        name = str(row.audio)
        audio_path = args.audio_dir / Path(name).name
        try:
            if not audio_path.is_file():
                raise FileNotFoundError(audio_path)
            prediction = model.transcribe(str(audio_path), language="vi", fp16=False)["text"].strip()
            reference = str(row.text)
            ref = normalize_vietnamese_text(reference)
            hyp = normalize_vietnamese_text(prediction)
            results.append({"audio": name, "ground_truth": reference, "prediction": prediction,
                            "wer": wer(ref, hyp), "cer": cer(ref, hyp), "error": ""})
            print(f"[{i}/{len(df)}] {name}: WER={results[-1]['wer']:.4f}")
        except Exception as exc:
            print(f"[{i}/{len(df)}] {name}: {exc}")
            results.append({"audio": name, "ground_truth": str(row.text), "prediction": "",
                            "wer": None, "cer": None, "error": str(exc)})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(results).to_csv(args.output, index=False, encoding="utf-8-sig")
    print(f"Saved {len(results)} rows to {args.output}")

if __name__ == "__main__":
    main()
