# Phân tích lỗi nhận dạng tiếng Việt — Wav2Vec2

Ứng dụng gồm **React + FastAPI**, chỉ sử dụng mô hình nhận dạng tiếng nói
**Wav2Vec2 tiếng Việt** với checkpoint
`khanhld/wav2vec2-base-vietnamese-160h`.

## Chức năng

- Nhận dạng MP3, WAV và bản thu trực tiếp từ microphone bằng Wav2Vec2.
- Xem kết quả đánh giá **1.000 mẫu Common Voice** cùng file audio gốc.
- Thống kê tỷ lệ lỗi từ (WER), tỷ lệ lỗi ký tự (CER), các loại lỗi từ.
- So sánh câu chuẩn với câu nhận dạng, phân tích lỗi âm đầu, âm chính, âm cuối và thanh điệu.
- Giao diện chỉ có một mô hình; không có tùy chọn hoặc biểu đồ so sánh mô hình khác.

## Dữ liệu và kết quả

- `dataset/audio/`: 1.000 file MP3.
- `dataset/metadata.csv`: danh sách audio và câu chuẩn.
- `dataset/asr_results_wav2vec2.csv`: kết quả Wav2Vec2 đã lưu.
- `dataset/sentence_analysis_wav2vec2.json`: phân tích theo câu.
- `dataset/error_statistics_wav2vec2.json`: thống kê toàn bộ.

Theo kết quả CSV đã lưu: WER trung bình **8,32%**, CER trung bình **3,04%**
và corpus WER **8,63%** trên chính bộ 1.000 mẫu này. Đây không phải kết quả
mới chạy lại trên Render và không đại diện mọi miền tiếng Việt. Chưa có bằng
chứng dự án tự huấn luyện lại checkpoint này.

## Chạy trên Windows

Yêu cầu Python với PyTorch/Transformers tương thích, Node.js, FFmpeg.
Dùng hai cửa sổ CMD.

CMD thứ nhất:

```cmd
cd /d E:\CSE457_Audio_Processing\Vietnamese-ASR-Analyzer
python -m pip install -r requirements-asr.txt
cd web\backend
python -m uvicorn main:app --reload
```

CMD thứ hai:

```cmd
cd /d E:\CSE457_Audio_Processing\Vietnamese-ASR-Analyzer\web\frontend
npm ci
npm run dev
```

Truy cập `http://localhost:5173`. API phát triển chạy trên
`http://127.0.0.1:8000`. Mô hình Wav2Vec2 tải khi nhận dạng mẫu mới đầu tiên.

## Tạo lại thống kê từ CSV hiện có

Chạy trong thư mục `Vietnamese-ASR-Analyzer`:

```cmd
python code\generate_sentence_analysis.py
python code\generate_error_statistics.py
```

Các lệnh này không huấn luyện hay chạy lại Wav2Vec2 trên 1.000 MP3.

## Kiểm thử

```cmd
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
cd web\frontend
npm ci
npm run lint
npm run build
```

CI kiểm tra chức năng API bằng mock; kiểm tra thực tế phải chạy thử MP3
với checkpoint Wav2Vec2.

## Docker và Render Free

`Dockerfile` đóng gói giao diện React, FastAPI, FFmpeg và Wav2Vec2
trong **một web service**. Triển khai dự kiến qua `../render.yaml`
dùng **Render Free**. Đây là cấu hình để thử nghiệm, không bảo đảm RAM
512 MB đủ cho PyTorch + Wav2Vec2. Nếu hết RAM cần máy mạnh hơn hoặc
Cloudflare Tunnel dùng CPU trên máy cá nhân.

```cmd
cd /d E:\CSE457_Audio_Processing\Vietnamese-ASR-Analyzer
docker build -t vietnamese-asr-wav2vec2:local .
docker run --rm -p 10000:10000 vietnamese-asr-wav2vec2:local
```

Truy cập `http://localhost:10000`, `/health`, `/ready`. Sau đó
**phải thử nhận dạng MP3 thực** để kiểm tra model tải và suy luận.

Xem [hướng dẫn Render Docker](docs/RENDER_DOCKER.md).
