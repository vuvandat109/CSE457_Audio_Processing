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
    """Git clone has no Common Voice clips; JSON dashboard still works."""
    stats = client.get("/api/statistics")
    assert stats.status_code == 200
    assert stats.json()["total_audio"] == 20
    assert stats.json()["average_wer"] == 0.4118
    listing = client.get("/api/audio-list")
    assert listing.status_code == 200
    items = listing.json()["data"]
    assert len(items) == 20
    assert all(x["audio_available"] is False for x in items)
    detail = client.get("/api/audio-detail/" + items[0]["audio"])
    assert detail.status_code == 200
    assert detail.json()["audio_available"] is False

def test_saved_results_are_consistent():
    summary = json.loads((ROOT / "dataset" / "summary_report.json").read_text())
    analysis = json.loads((ROOT / "dataset" / "sentence_analysis.json").read_text())
    assert len(analysis["data"]) == summary["tong_quan"]["so_luong_audio"]
    assert round(sum(x["wer"] for x in analysis["data"]) / len(analysis["data"]), 4) == summary["tong_quan"]["WER_trung_binh"]
    assert round(sum(x["cer"] for x in analysis["data"]) / len(analysis["data"]), 4) == summary["tong_quan"]["CER_trung_binh"]
