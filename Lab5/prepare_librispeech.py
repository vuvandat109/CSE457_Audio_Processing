"""Extract the documented LibriSpeech subset from the official dev-clean archive."""
import argparse
import csv
from pathlib import Path
import subprocess
import tarfile

import numpy as np
from scipy.io import wavfile

ROOT = Path(__file__).resolve().parent / "lab5_data"
SPEAKERS = ("652", "174", "251")
COUNTS = (("enroll", 4), ("dev", 2), ("test", 4))
SR = 16000


def decode(encoded):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", "pipe:0", "-ac", "1", "-ar", str(SR),
         "-f", "s16le", "pipe:1"],
        input=encoded, capture_output=True, check=True
    ).stdout
    return np.frombuffer(raw, dtype="<i2")


def main(path):
    for folder in ("clean", "separation"):
        (ROOT / folder).mkdir(parents=True, exist_ok=True)
    records = []
    with tarfile.open(path, "r|gz") as archive:
        by_speaker = {speaker: {} for speaker in SPEAKERS}
        for member in archive:
            parts = Path(member.name).parts
            if len(parts) == 5 and parts[2] in by_speaker and member.name.endswith(".flac"):
                by_speaker[parts[2]].setdefault(parts[3], []).append((member, archive.extractfile(member).read()))
        for index, speaker in enumerate(SPEAKERS, 1):
            chapters = by_speaker[speaker]
            chapter_sets = {}
            for chapter, members in sorted(chapters.items()):
                accepted = []
                for member, encoded in sorted(members, key=lambda item: item[0].name):
                    samples = decode(encoded)
                    if 2 * SR <= samples.size <= 4 * SR and np.any(samples):
                        accepted.append((member, samples))
                    if len(accepted) == 6:
                        break
                chapter_sets[chapter] = accepted
            enroll_chapter, test_chapter = next(
                (a, b) for a in chapter_sets for b in chapter_sets
                if a != b and len(chapter_sets[a]) >= 4 and len(chapter_sets[b]) >= 6
            )
            heldout = chapter_sets[test_chapter]
            partitions = (chapter_sets[enroll_chapter][:4], heldout[:2], heldout[2:6])
            for (split, count), items in zip(COUNTS, partitions):
                assert len(items) == count
                for number, (member, samples) in enumerate(items, 1):
                    name = f"spk{index:02}_{split}_{number:02}.wav"
                    wavfile.write(ROOT / "clean" / name, SR, samples)
                    records.append((name, split, speaker, Path(member.name).parent.name,
                                    member.name, f"{len(samples) / SR:.4f}"))
    with (ROOT / "sources.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("local_file", "split", "librispeech_speaker", "chapter",
                         "archive_member", "duration_s"))
        writer.writerows(records)
    for letter, filename in [("A", "spk01_test_01.wav"), ("B", "spk02_test_02.wav")]:
        (ROOT / "separation" / f"source_{letter}.wav").write_bytes(
            (ROOT / "clean" / filename).read_bytes()
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    main(parser.parse_args().archive)
