# -*- coding: utf-8 -*-
"""Summarize a fresh, verified batch; never mix with historical dashboard results.

python code/report_three_models_1000.py --input-dir dataset/evaluation_recheck
"""
import argparse
import csv
import json
import html
from pathlib import Path

MODELS = ("whisper", "phowhisper", "wav2vec2")
DISPLAY = {"whisper": "Whisper base", "phowhisper": "PhoWhisper base",
           "wav2vec2": "Wav2Vec2 Vietnamese"}


def summary_for_model(path, count, ordered_names):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != count or [r["audio"] for r in rows] != ordered_names:
        raise ValueError(f"{path.name}: expected exactly {count} ordered audio rows; no omissions/duplicates")
    failures = [r for r in rows if r["status"] != "ok"]
    if failures:
        raise ValueError(f"{path.name}: {len(failures)} failures; retry before reporting")
    wer = [float(r["wer"]) for r in rows]
    cer = [float(r["cer"]) for r in rows]
    return {
        "model": path.stem.removeprefix("results_"),
        "samples": count,
        "mean_wer": sum(wer) / count,
        "mean_cer": sum(cer) / count,
        "exact_matches": sum(w == 0 and c == 0 for w, c in zip(wer, cer)),
        "mean_seconds_including_load": sum(float(r["seconds"]) for r in rows) / count,
        "worst_samples": sorted(
            [{"audio": x["audio"], "reference": x["ground_truth"],
              "prediction": x["prediction"], "wer": float(x["wer"])} for x in rows],
            key=lambda x: x["wer"], reverse=True)[:10],
    }


def svg_chart(results, metric, title):
    width, height = 870, 300
    maximum = max([x[metric] for x in results] + [0.001])
    scale = 580 / maximum
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             f'<text x="25" y="35" font-family="Arial" font-size="20" font-weight="bold">{html.escape(title)}</text>']
    for i, row in enumerate(results):
        y = 65 + i * 70
        label = html.escape(DISPLAY[row["model"]])
        value = row[metric] * 100
        bar_width = max(1, row[metric] * scale)
        parts += [f'<text x="25" y="{y+24}" font-family="Arial" font-size="15">{label}</text>',
                  f'<rect x="225" y="{y}" width="{bar_width:.2f}" height="35" fill="#2563eb"/>',
                  f'<text x="{min(820, 235+bar_width):.2f}" y="{y+24}" font-family="Arial" font-size="15">{value:.2f}%</text>']
    parts.append('</svg>')
    return "\n".join(parts)


def generate(folder, require_1000=True):
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    names = manifest["audio_names"]
    count = len(names)
    if count != manifest["limit"]:
        raise ValueError("Manifest count mismatch")
    if require_1000 and count != 1000:
        raise ValueError(f"Only {count} samples; full report requires 1000 (use --allow-partial for testing)")
    results = [summary_for_model(folder / f"results_{m}.csv", count, names) for m in MODELS]
    (folder / "verified_comparison.json").write_text(
        json.dumps({"source": "fresh_checkpoint_inference", "samples": count, "models": results},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    for metric in ("mean_wer", "mean_cer"):
        (folder / f"chart_{metric}.svg").write_text(svg_chart(results, metric, f"{metric.upper()} comparison ({count} clips)"),
                                                       encoding="utf-8")
    lines = [
        "# Báo cáo thực nghiệm nhận dạng tiếng nói tiếng Việt",
        "",
        f"**Nguồn kết quả:** suy luận lại bằng checkpoint trên {count} MP3; không phải số liệu CSV lịch sử.",
        "**Mô hình:** Whisper base, vinai/PhoWhisper-base, khanhld/wav2vec2-base-vietnamese-160h.",
        "**Dữ liệu:** dataset/metadata.csv và dataset/audio/ (cùng thứ tự, cùng câu chuẩn).",
        "**Phương pháp:** chọn ngôn ngữ tiếng Việt; so sánh dự đoán với câu chuẩn, chuẩn hóa chữ thường và dấu câu theo audio_analyzer.calculate_score.",
        "Các giá trị WER/CER trung bình tính trên câu; đây không phải corpus WER. WER/CER thấp hơn là tốt hơn.",
        "",
        "## Kết quả",
        "| Mô hình | Số mẫu | WER trung bình | CER trung bình | Đúng hoàn toàn |",
        "|---|---:|---:|---:|---:|",
    ]
    for x in results:
        lines.append(f'| {DISPLAY[x["model"]]} | {count} | {100*x["mean_wer"]:.2f}% | {100*x["mean_cer"]:.2f}% | {x["exact_matches"]} |')
    lines += ["", "![WER](chart_mean_wer.svg)", "", "![CER](chart_mean_cer.svg)",
              "", "## Một số trường hợp nhận dạng sai"]
    for x in results:
        lines += ["", f'### {DISPLAY[x["model"]]}']
        for row in x["worst_samples"][:3]:
            lines += [f'- `{row["audio"]}` — WER {row["wer"]*100:.2f}%',
                      f'  - Câu chuẩn: {row["reference"]}',
                      f'  - Dự đoán: {row["prediction"]}']
    lines += ["", "## Giới hạn",
              "- Kết quả chỉ áp dụng cho 1.000 câu trong tập hiện tại, không khẳng định hiệu quả trên mọi miền dữ liệu.",
              "- Không có huấn luyện hoặc fine-tuning trong thử nghiệm này; sử dụng checkpoint công khai.",
              "- Thời gian chạy bao gồm thời gian tải/khởi tạo model nếu xảy ra và không dùng để so sánh inference thuần túy.",
              "- CSV lịch sử phục vụ giao diện chưa được ghi đè. Báo cáo này được tạo riêng từ kết quả kiểm chứng.",
              ""]
    (folder / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path(__file__).resolve().parents[1] / "dataset" / "evaluation_recheck")
    parser.add_argument("--allow-partial", action="store_true", help="Permit a small trial report; never present as full evaluation")
    args = parser.parse_args(argv)
    results = generate(args.input_dir.resolve(), require_1000=not args.allow_partial)
    for row in results:
        print(f'{DISPLAY[row["model"]]}: WER={row["mean_wer"]:.4f}, CER={row["mean_cer"]:.4f}, exact={row["exact_matches"]}')
    print(f"Report: {args.input_dir / 'REPORT.md'}")


if __name__ == "__main__":
    main()
