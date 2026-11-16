# Lab 5 · Xử lý âm thanh và tiếng nói

Bài thực hành CSE457 “Trợ lý phòng họp mini” gồm khử nhiễu tiếng nói,
nhận dạng và xác minh người nói, và tách hai người nói chồng lấn bằng FastICA.

[Hướng dẫn từng bước và cách đọc kết quả](HUONG_DAN_CHI_TIET.md)

## Chạy trên Windows

1. Giải nén ZIP rồi mở thư mục `Lab5` trong VS Code.
2. Mở **Terminal → New Terminal** và chạy lần lượt các lệnh dưới đây.
   Dùng Python 3.11 hoặc 3.12.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe Lab5.py
```

Nếu cài Python 3.11, thay `-3.12` bằng `-3.11`.
Trên macOS/Linux, dùng `python3 -m venv .venv` và `.venv/bin/python`.

Khi thấy `Lab 5 complete`, mở `results/` để kiểm tra WAV, PNG và số liệu.
Chương trình dùng đường dẫn theo vị trí file `Lab5.py` và tạo lại kết quả khi chạy.

## Dữ liệu

- 30 bản thu giọng thật từ ba người đọc trong LibriSpeech dev-clean.
  Mỗi người có 4 đoạn đăng ký, 2 dev và 4 test. Enrollment lấy từ chương
  khác nhóm dev/test.
- `lab5_data/sources.csv` truy xuất mã người nói, chương và đường dẫn gốc.
  `lab5_data/ATTRIBUTION.md` ghi nguồn và giấy phép. Giữ file này khi đưa lên Git.
- WAV đã kèm sẵn. Để trích lại dữ liệu, tải `dev-clean.tar.gz` từ địa chỉ
  OpenSLR ghi trong ATTRIBUTION, cài FFmpeg và chạy `python prepare_librispeech.py dev-clean.tar.gz`.
- `python generate_noise.py` tạo lại tín hiệu quạt mô phỏng.

## Xem kết quả

| Tệp | Nội dung |
|---|---|
| `report.pdf` | Báo cáo 5 trang, công thức, số liệu, 12 câu hỏi |
| `results/audio/` | Clean, noisy, Spectral Subtraction, Wiener, hai mic và hai nguồn tách |
| `results/audio/ablation/` | WAV để đối chiếu các giá trị β, γ và các cấu hình ICA |
| `results/figures/` | Waveform, spectrogram, confusion matrix, FAR–FRR và tương quan ICA |
| `results/enhancement.csv` | Công suất, RMS, hệ số nhiễu, SNR và toàn bộ 27 tổ hợp tham số |
| `results/enhancement_test_clips.csv`, `enhancement_frame_diagnostics.csv` | SNR từng đoạn test và RMS sai số tại vùng yên/vùng có tiếng nói |
| `results/speaker_scores.csv` | Điểm cosine cho từng đoạn test, từng điều kiện và từng giọng |
| `results/speaker_conditions.csv`, `speaker_ablation.csv` | Accuracy và khoảng cách điểm đúng với đối thủ cao nhất |
| `results/verification_*.csv`, `summary.json` | Trials, đường cong dev, ngưỡng và FAR/FRR dev/test |
| `results/ica.csv` | Định thức, số điều kiện, tương quan và SI-SDR trước/sau tách |
| `results/speaker_models.npz` | Ba centroid và nhãn giọng |

Để đối chiếu bằng tai, mở lần lượt `clean.wav`, `noisy.wav`,
`enhanced_ss.wav`, `enhanced_wiener.wav` ở cùng âm lượng. Nghe tiếng quạt
giữa từ, độ rõ phụ âm và âm rít ngắn. Với ICA, nghe `mix_mic1.wav` rồi
`separated_1.wav` và `separated_2.wav` để kiểm tra giọng còn lẫn.

## Đưa lên GitHub

1. Giải nén và mở thư mục `Lab5`.
2. Trong repository trên GitHub, chọn **Add file → Upload files**.
3. Kéo các tệp và thư mục **bên trong** `Lab5` vào trang, rồi chọn **Commit changes**.
   Nếu đã clone repository xuống máy, bạn cũng có thể chép bộ tệp vào thư mục clone
   và dùng `git add .`, `git commit -m "Add Lab 5 audio processing"`, `git push`.
