"""Regression tests for the Wav2Vec2-only dashboard and upload API."""
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
MODEL = "wav2vec2"


def test_single_model_only():
    models = client.get("/api/models")
    assert models.status_code == 200
    assert models.json()["default"] == MODEL
    assert [entry["key"] for entry in models.json()["models"]] == [MODEL]
    assert client.get("/api/statistics", params={"model": "whisper"}).status_code in (400, 422)
    assert client.get("/api/statistics", params={"model": "phowhisper"}).status_code in (400, 422)
    assert client.get("/api/model-comparison").status_code == 404


def test_dashboard_on_1000_audio_samples():
    stats = client.get("/api/statistics", params={"model": MODEL})
    assert stats.status_code == 200
    assert stats.json()["total_audio"] == 1000
    listing = client.get("/api/audio-list", params={"model": MODEL})
    assert listing.status_code == 200
    items = listing.json()["data"]
    assert len(items) == 1000
    assert all(x["audio_available"] == (ROOT / "dataset" / "audio" / x["audio"]).is_file() for x in items)
    detail = client.get("/api/audio-detail/" + items[0]["audio"], params={"model": MODEL})
    assert detail.status_code == 200


def test_saved_wav2vec2_results_are_consistent():
    analysis = json.loads((ROOT / "dataset" / "sentence_analysis_wav2vec2.json").read_text(encoding="utf-8"))
    assert len(analysis["data"]) == 1000
    assert all(isinstance(x["wer"], (int, float)) and x["wer"] >= 0 for x in analysis["data"])
    assert all(isinstance(x["cer"], (int, float)) and x["cer"] >= 0 for x in analysis["data"])


def test_upload_with_wav2vec2(monkeypatch):
    calls = []
    def fake_transcribe(path, model):
        assert path.is_file()
        calls.append(model)
        return "xin chào"
    monkeypatch.setattr(module, "transcribe_audio", fake_transcribe)
    response = client.post(
        "/api/test-audio",
        data={"model": MODEL, "ground_truth": "xin chào"},
        files={"file": ("sample.mp3", b"wav2vec2 unique mock audio", "audio/mpeg")},
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["model"] == MODEL
    assert result["wer"] == 0
    assert result["cer"] == 0
    assert calls == [MODEL]


def test_upload_without_reference(monkeypatch):
    monkeypatch.setattr(module, "transcribe_audio", lambda path, model: "kết quả")
    response = client.post(
        "/api/v1/asr/transcribe",
        files={"file": ("sample.wav", b"new raw bytes", "audio/wav")},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["model"] == MODEL
    assert result["status"] == "unscored"
    assert result["prediction"] == "kết quả"
    assert result["has_ground_truth"] is False


def test_upload_rejects_old_models_and_invalid_files(monkeypatch):
    def unexpected_inference(*args, **kwargs):
        raise AssertionError("Inference should not run for invalid inputs")
    monkeypatch.setattr(module, "transcribe_audio", unexpected_inference)
    for old in ("whisper", "phowhisper", "unknown"):
        invalid = client.post(
            "/api/test-audio",
            data={"model": old},
            files={"file": ("audio.mp3", b"data", "audio/mpeg")},
        )
        assert invalid.status_code == 400
    bad_extension = client.post(
        "/api/test-audio",
        files={"file": ("sample.txt", b"data", "text/plain")},
    )
    assert bad_extension.status_code == 400
    empty = client.post(
        "/api/test-audio",
        files={"file": ("sample.mp3", b"", "audio/mpeg")},
    )
    assert empty.status_code == 400


def test_inference_failure(monkeypatch):
    def broken(path, model):
        raise RuntimeError("test-only inference failure")
    monkeypatch.setattr(module, "transcribe_audio", broken)
    response = client.post(
        "/api/test-audio",
        files={"file": ("sample.mp3", b"new fail bytes", "audio/mpeg")},
    )
    assert response.status_code == 500
    assert "test-only inference failure" in response.json()["detail"]


def test_cached_result_recomputes_ground_truth(monkeypatch):
    calls = []
    def fake(path, model):
        calls.append(model)
        return "xin chào"
    monkeypatch.setattr(module, "transcribe_audio", fake)
    payload = b"wav2vec2 unique cache regression sample"
    def send(text):
        return client.post(
            "/api/test-audio",
            data={"model": MODEL, "ground_truth": text},
            files={"file": ("cached.mp3", payload, "audio/mpeg")},
        )
    first, second = send("xin chào"), send("xin tạm biệt")
    assert first.status_code == 200 and second.status_code == 200
    assert first.json()["cached"] is False
    assert second.json()["cached"] is True
    assert len(calls) == 1
    assert first.json()["wer"] == 0
    assert second.json()["wer"] > 0


def test_production_root_serves_react_html(tmp_path, monkeypatch):
    (tmp_path / "index.html").write_text(
        "<!doctype html><html lang='vi'><body>Wav2Vec2</body></html>",
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "FRONTEND_DIST", tmp_path)
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Wav2Vec2" in response.text
