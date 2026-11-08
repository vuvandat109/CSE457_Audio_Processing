import importlib.util
import json
import sys
from pathlib import Path
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "web" / "backend"
sys.path.insert(0, str(BACKEND))
spec = importlib.util.spec_from_file_location("asr_dashboard_main", BACKEND / "main.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
client = TestClient(module.app)

def test_dashboard_without_audio_clips():
    """Dashboard exposes the current 1,000-result datasets without local MP3s."""
    models = client.get("/api/models")
    assert models.status_code == 200
    assert {x["key"] for x in models.json()["models"]} == {
        "whisper", "phowhisper", "wav2vec2"
    }
    for model in ("whisper", "phowhisper", "wav2vec2"):
        stats = client.get("/api/statistics", params={"model": model})
        assert stats.status_code == 200
        assert stats.json()["total_audio"] == 1000
        listing = client.get("/api/audio-list", params={"model": model})
        assert listing.status_code == 200
        items = listing.json()["data"]
        assert len(items) == 1000
        assert all(not x["audio_available"] for x in items)
        detail = client.get("/api/audio-detail/" + items[0]["audio"], params={"model": model})
        assert detail.status_code == 200
        assert detail.json()["audio_available"] is False


def test_saved_results_are_consistent():
    """All 3 models have matching per-sentence analysis and statistics."""
    comparison = json.loads((ROOT / "dataset" / "model_comparison.json").read_text(encoding="utf-8"))
    assert len(comparison["models"]) == 3
    for model in comparison["models"]:
        assert model["total_audio"] == 1000
        assert model["valid_wer_samples"] == 1000
        assert model["valid_cer_samples"] == 1000
        key = model["key"]
        suffix = ("whisper" if key == "whisper_base"
                  else "phowhisper" if key == "phowhisper_base"
                  else "wav2vec2")
        analysis = json.loads(
            (ROOT / "dataset" / f"sentence_analysis_{suffix}.json").read_text(encoding="utf-8")
        )
        values = analysis["data"]
        assert len(values) == 1000
        assert all(isinstance(x["wer"], (int, float)) and x["wer"] >= 0 for x in values)
        assert all(isinstance(x["cer"], (int, float)) and x["cer"] >= 0 for x in values)
        api_key = "whisper" if suffix == "whisper" else suffix
        stats = client.get("/api/statistics", params={"model": api_key}).json()
        assert abs(stats["average_wer"] - model["average_wer"]) < 1e-9
        assert abs(stats["average_cer"] - model["average_cer"]) < 1e-9
