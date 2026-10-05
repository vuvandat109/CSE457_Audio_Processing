# CSE457 - Lab 2: Đặc trưng tiếng nói và nhận dạng bằng DTW

Project hoàn chỉnh bám theo Lab 2: **MFCC + Dynamic Time Warping (DTW)** cho nhận dạng 5 từ tiếng Việt tách rời.

## 1. Dataset đúng cấu trúc Lab

Vocabulary: **không, một, hai, ba, bốn**. Mỗi lớp có **5 file WAV**; 3 file đầu dùng làm template train và 2 file cuối dùng test.

- WAV mono, PCM 16-bit, 16 kHz.
- Mỗi file có khoảng 0.2-0.5 s silence ở đầu/cuối để kiểm tra endpoint detection.
- Tên thư mục/file dùng ASCII: `khong`, `mot`, `hai`, `ba`, `bon`.
- Tổng cộng: 25 file = 5 lớp × 5 lần.

> **Minh bạch dữ liệu:** các file lời nói trong repository được tạo bằng giọng tổng hợp tiếng Việt (eSpeak), không phải giọng thu âm cá nhân của sinh viên. Chúng phù hợp để chạy/kiểm thử toàn bộ pipeline. Nếu giảng viên yêu cầu dữ liệu tự thu, hãy thay 25 file bằng bản ghi thật của bạn và chạy lại notebook.

## 2. Nội dung đã thực hiện

- Kiểm tra waveform của 3 từ, clipping, silence.
- Framing 25 ms, hop 10 ms, Hamming window.
- Short-time energy, magnitude, RMS, log-energy và ZCR.
- Endpoint detection tự xây dựng dựa trên log-energy, có ZCR hỗ trợ tinh chỉnh biên và margin 50 ms.
- Short-time autocorrelation và ước lượng pitch minh họa.
- Pre-emphasis α=0.97.
- MFCC: NFFT=512, 24 Mel filters, 13 hệ số + CMN.
- Euclidean local distance.
- DTW tự cài bằng dynamic programming, backtracking và chuẩn hóa theo path length.
- Nearest-template: 3 template/lớp, 2 test/lớp.
- Top-3 nhãn gần nhất cho tất cả file test.
- Accuracy + confusion matrix.
- E1: có endpoint detection so với không endpoint.
- E2: 13 MFCC so với MFCC + Δ.
- Trả lời đầy đủ 9 câu hỏi báo cáo trong notebook/report.

## 3. Kết quả hiện tại trên dataset tổng hợp

- Baseline accuracy: **100.0%**
- DTW_norm cùng từ (`mot_01` vs `mot_04`): **15.867**
- DTW_norm khác từ (`mot_01` vs `bon_04`): **46.629**

Các số này chỉ phản ánh dataset tổng hợp đi kèm, không nên coi là kết quả đại diện cho speech tự nhiên.

## 4. Cấu trúc repository

```text
Lab2_MFCC_DTW_Complete/
├── Lab2_MFCC_DTW.ipynb
├── Lab2_Report.md
├── Lab2_Report.pdf
├── README.md
├── requirements.txt
├── run_lab.py
├── dataset/
│   ├── khong/   (khong_01.wav ... khong_05.wav)
│   ├── mot/     (mot_01.wav ... mot_05.wav)
│   ├── hai/     (hai_01.wav ... hai_05.wav)
│   ├── ba/      (ba_01.wav ... ba_05.wav)
│   └── bon/     (bon_01.wav ... bon_05.wav)
├── src/lab2_pipeline.py
├── figures/
├── trimmed_samples/
├── sample_input/audio_10s_16khz_mono.wav
├── results.csv
├── experiment_results.csv
├── endpoint_results.csv
├── dataset_metadata.csv
├── audio_validation.csv
└── summary.json
```

## 5. Chạy project

```bash
python -m venv .venv
```
Windows:
```bash
.venv\Scripts\activate
```
Cài thư viện:
```bash
pip install -r requirements.txt
```
Chạy nhanh:
```bash
python run_lab.py
```
Hoặc mở `Lab2_MFCC_DTW.ipynb` trong Jupyter/VS Code và **Run All**.

## 6. Đưa lên Git

```bash
git init
git add .
git commit -m "Complete CSE457 Lab 2 MFCC DTW"
git branch -M main
git remote add origin <URL_REPOSITORY>
git push -u origin main
```
