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
        assert all(x["audio_available"] == (ROOT / "dataset" / "audio" / x["audio"]).is_file() for x in items)
        detail = client.get("/api/audio-detail/" + items[0]["audio"], params={"model": model})
        assert detail.status_code == 200
        assert detail.json()["audio_available"] == (ROOT / "dataset" / "audio" / items[0]["audio"]).is_file()


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


def test_upload_with_each_model(monkeypatch):
    """API upload reaches the selected engine; avoid downloading model weights in CI."""
    calls = []

    def fake_transcribe(path, model):
        assert path.is_file()
        assert path.read_bytes() == b"mock audio bytes"
        calls.append(model)
        return "xin chào"

    monkeypatch.setattr(module, "transcribe_audio", fake_transcribe)
    for model in ("whisper", "phowhisper", "wav2vec2"):
        response = client.post(
            "/api/test-audio",
            data={"model": model, "ground_truth": "xin chào"},
            files={"file": ("sample.mp3", b"mock audio bytes", "audio/mpeg")},
        )
        assert response.status_code == 200, response.text
        result = response.json()
        assert result["model"] == model
        assert result["prediction"] == "xin chào"
        assert result["status"] == "correct"
        assert result["wer"] == 0
        assert result["cer"] == 0
        assert result["has_ground_truth"] is True
    assert calls == ["whisper", "phowhisper", "wav2vec2"]


def test_upload_without_reference(monkeypatch):
    monkeypatch.setattr(module, "transcribe_audio", lambda path, model: "kết quả")
    response = client.post(
        "/api/v1/asr/transcribe",
        data={"model": "whisper"},
        files={"file": ("sample.wav", b"nonempty", "audio/wav")},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "unscored"
    assert result["prediction"] == "kết quả"
    assert result["has_ground_truth"] is False
    assert result["wer"] is None
    assert result["cer"] is None


def test_upload_rejects_invalid_model_and_files(monkeypatch):
    def unexpected_inference(*args, **kwargs):
        raise AssertionError("Inference should not run for invalid inputs")

    monkeypatch.setattr(module, "transcribe_audio", unexpected_inference)
    invalid_model = client.post(
        "/api/test-audio",
        data={"model": "unknown"},
        files={"file": ("audio.mp3", b"data", "audio/mpeg")},
    )
    assert invalid_model.status_code == 400
    invalid_extension = client.post(
        "/api/test-audio",
        data={"model": "whisper"},
        files={"file": ("sample.txt", b"data", "text/plain")},
    )
    assert invalid_extension.status_code == 400
    empty_file = client.post(
        "/api/test-audio",
        data={"model": "whisper"},
        files={"file": ("sample.mp3", b"", "audio/mpeg")},
    )
    assert empty_file.status_code == 400


def test_upload_reports_inference_failure(monkeypatch):
    def broken_inference(path, model):
        raise RuntimeError("test-only inference failure")

    monkeypatch.setattr(module, "transcribe_audio", broken_inference)
    response = client.post(
        "/api/test-audio",
        data={"model": "phowhisper"},
        files={"file": ("sample.mp3", b"data", "audio/mpeg")},
    )
    assert response.status_code == 500
    assert "test-only inference failure" in response.json()["detail"]


def test_repeated_upload_is_cached_but_ground_truth_is_rescored(monkeypatch):
    calls = []
    def fake_inference(path, model):
        calls.append(model)
        return "xin chào"
    monkeypatch.setattr(module, "transcribe_audio", fake_inference)
    payload = b"unique cached audio sample for regression"
    first = client.post(
        "/api/test-audio",
        data={"model": "phowhisper", "ground_truth": "xin chào"},
        files={"file": ("cached.mp3", payload, "audio/mpeg")},
    )
    second = client.post(
        "/api/test-audio",
        data={"model": "phowhisper", "ground_truth": "xin tạm biệt"},
        files={"file": ("cached.mp3", payload, "audio/mpeg")},
    )
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json()["cached"] is False
    assert second.json()["cached"] is True
    assert len(calls) == 1
    assert first.json()["wer"] == 0
    assert second.json()["wer"] > 0
