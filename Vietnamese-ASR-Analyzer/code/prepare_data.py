"""Select Common Voice clips and generate audio/text metadata."""
import argparse
import shutil
from pathlib import Path
import pandas as pd

DATASET_DIR = Path(__file__).resolve().parents[1] / "dataset"

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tsv", type=Path, required=True, help="Common Voice vi/validated.tsv")
    parser.add_argument("--clips", type=Path, required=True, help="Common Voice vi/clips directory")
    parser.add_argument("--output-dir", type=Path, default=DATASET_DIR)
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be positive")
    df = pd.read_csv(args.tsv, sep="\t", encoding="utf-8")
    required = {"path", "sentence", "up_votes", "down_votes"}
    if not required.issubset(df.columns):
        parser.error(f"Missing TSV columns: {required - set(df.columns)}")
    df = df[(df["up_votes"] >= 2) & (df["down_votes"] == 0)]
    selected = df.sample(n=min(args.limit, len(df)), random_state=args.seed)
    audio_dir = args.output_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for row in selected.itertuples(index=False):
        source = args.clips / Path(str(row.path)).name
        if source.is_file():
            shutil.copy2(source, audio_dir / source.name)
            rows.append({"audio": source.name, "text": row.sentence})
    pd.DataFrame(rows, columns=["audio", "text"]).to_csv(
        args.output_dir / "metadata.csv", index=False, encoding="utf-8-sig")
    print(f"Prepared {len(rows)} clips in {audio_dir}")

if __name__ == "__main__":
    main()
