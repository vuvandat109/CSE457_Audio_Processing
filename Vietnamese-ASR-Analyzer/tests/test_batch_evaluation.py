"""Regression tests for resume-safe model evaluation and strict reporting."""
import csv
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / (name + ".py"))
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def test_batch_resume_three_models_and_verified_report(tmp_path, monkeypatch):
    evaluator = load_script("evaluate_three_models_1000")
    report = load_script("report_three_models_1000")
    dataset = tmp_path / "dataset"
    (dataset / "audio").mkdir(parents=True)
    with (dataset / "metadata.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["audio", "text"])
        writer.writerow(["one.mp3", "xin chào"])
        writer.writerow(["two.mp3", "tôi đi"])
    for name in ("one.mp3", "two.mp3"):
        (dataset / "audio" / name).write_bytes(b"fake audio for mocked inference")
    monkeypatch.setattr(evaluator, "ROOT", tmp_path)
    calls = []
    def fake_transcribe(path, model):
        calls.append((path.name, model))
        return {"one.mp3": "xin chào", "two.mp3": "tôi đi"}[path.name]

    output = tmp_path / "fresh"
    args = ["--limit", "2", "--output-dir", str(output)]
    assert evaluator.main(args, transcribe=fake_transcribe) == 0
    assert len(calls) == 6
    assert evaluator.main(args, transcribe=fake_transcribe) == 0
    assert len(calls) == 6, "Completed rows must not be re-inferred"
    summary = report.generate(output, require_1000=False)
    assert len(summary) == 3
    assert all(row["exact_matches"] == 2 for row in summary)
    assert all(row["mean_wer"] == 0 for row in summary)
    assert (output / "REPORT.md").exists()
    assert (output / "chart_mean_cer.svg").exists()
    assert (output / "verified_comparison.json").exists()


def test_report_rejects_incomplete_results(tmp_path):
    report = load_script("report_three_models_1000")
    folder = tmp_path / "recheck"
    folder.mkdir()
    (folder / "manifest.json").write_text(
        json.dumps({"limit": 1, "audio_names": ["one.mp3"]}), encoding="utf-8")
    for model in report.MODELS:
        with (folder / f"results_{model}.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "audio", "ground_truth", "prediction", "wer", "cer", "status", "error", "seconds"
            ])
            writer.writeheader()
            writer.writerow(dict(audio="one.mp3", ground_truth="xin chào",
                                 prediction="", wer="", cer="", status="failed",
                                 error="test failure", seconds="0"))
    try:
        report.generate(folder, require_1000=False)
    except ValueError as exc:
        assert "failures" in str(exc)
    else:
        raise AssertionError("Incomplete results must never produce verified report")
