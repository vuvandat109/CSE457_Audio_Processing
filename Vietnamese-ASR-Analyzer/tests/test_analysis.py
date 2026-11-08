import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "web" / "backend"))
from audio_analyzer import calculate_score, word_alignment

def test_exact_match_and_tone_error():
    assert calculate_score("Tôi là sinh viên", "tôi là sinh viên") == {"wer": 0.0, "cer": 0.0}
    score = calculate_score("chạy", "chảy")
    assert score["wer"] == 1.0
    assert 0 < score["cer"] < 1

def test_word_alignment_edits():
    alignment = word_alignment("mời bạn đến", "mời khách bạn đến")
    assert any(x["type"] == "extra_word" and x["prediction"] == "khách" for x in alignment)
