# Vietnamese ASR Analyzer

Ứng dụng FastAPI + React để nhận dạng audio mới và xem kết quả đánh giá tiếng Việt trên 1.000 mẫu Common Voice. Giao diện có ba lựa chọn: **OpenAI Whisper base**, **vinai/PhoWhisper-base** và **Wav2Vec2 Vietnamese**. Chọn model trên web trước khi xem thống kê hoặc gửi audio mới. Model chỉ tải khi nhận dạng audio mới; dashboard đọc kết quả đã lưu.

## Nguồn dữ liệu và kết quả

Các tệp `dataset/asr_results.csv`, `asr_results_phowhisper.csv`, `asr_results_wav2vec2.csv` được đồng bộ từ bản `ASR_Project(1).zip` do chủ dự án cung cấp. Mỗi tệp có 1.000 dự đoán, không có dòng lỗi; tên audio và câu chuẩn khớp 1.000 dòng trong `dataset/metadata.csv`. JSON phân tích câu, thống kê và so sánh được tạo lại từ các CSV này. Đây là kiểm tra tính nhất quán của kết quả đã lưu, **không phải lần chạy suy luận model mới trong GitHub**. Audio gốc gồm 1.000 MP3 đã được đẩy vào `dataset/audio/`, có thể phát lại và dùng cho việc đánh giá lại. Các số liệu tổng hợp vẫn là kết quả CSV đã lưu, chưa phải phép suy luận lại toàn bộ từ các checkpoint trong GitHub.

| Model | WER trung bình theo câu | CER trung bình theo câu | Corpus WER |
| --- | ---: | ---: | ---: |
| Whisper base | 48,98% | 26,44% | 45,17% |
| PhoWhisper base | 10,57% | 4,75% | 9,78% |
| Wav2Vec2 Vietnamese | 8,32% | 3,04% | 8,63% |

WER/CER phụ thuộc cách chuẩn hóa và tách từ; đây là số liệu trên bộ 1.000 mẫu này, không đại diện toàn bộ Common Voice. Không có bằng chứng về quá trình huấn luyện lại model trong dự án: ba model dùng checkpoint đã có.

## Chạy web trên Windows CMD

Yêu cầu Python có môi trường tương thích với PyTorch/Transformers, Node.js 22+, FFmpeg có thể chạy bằng lệnh `ffmpeg -version`. Nếu đang dùng thư mục giải nén `E:\ASR_Project`, thay đường dẫn bên dưới cho phù hợp. Cửa sổ CMD 1:

```cmd
cd /d E:\ASR_Project
python -m pip install -r requirements-asr.txt
cd web\backend
python -m uvicorn main:app --reload
```

Cửa sổ CMD 2:

```cmd
cd /d E:\ASR_Project\web\frontend
npm ci
npm run dev
```

Mở http://localhost:5173 và API http://127.0.0.1:8000/docs. Nếu thiếu FFmpeg nhưng `pip` hoạt động, xem hướng dẫn tự động ở `docs/FFMPEG_WINDOWS.md`. Model được tải về ở lần nhận dạng mới đầu tiên; cần kết nối mạng và đủ dung lượng.

## Tái tạo thống kê từ CSV đã lưu

Tại thư mục gốc dự án:

```cmd
python code\generate_sentence_analysis.py --model all
python code\generate_error_statistics.py --model all
python code\generate_model_comparison.py
```

Để **chạy lại suy luận PhoWhisper trên 1.000 MP3 thật**, trước tiên đặt các MP3 đúng tên trong `dataset/audio/`, xác nhận `ffmpeg -version` và sao lưu CSV cũ. Sau đó:

```cmd
python code\batch_evaluate_phowhisper_1000.py
python code\generate_sentence_analysis.py --model phowhisper
python code\generate_error_statistics.py --model phowhisper
python code\generate_model_comparison.py
```

Lệnh đánh giá ghi đè CSV PhoWhisper. Kiểm tra số mẫu thành công/thất bại trước khi dùng số liệu mới.

## Kiểm thử chức năng website và nhận dạng thực tế

Chạy API từ thư mục `Vietnamese-ASR-Analyzer/web/backend` với `python -m uvicorn main:app --reload`, sau đó chạy frontend từ `web/frontend` với `npm ci` và `npm run dev`. Mở `http://localhost:5173`, chọn lần lượt Whisper / PhoWhisper / Wav2Vec2, tải lên một MP3 trong `dataset/audio/`, nhập câu gốc nếu muốn WER/CER, và kiểm tra câu dự đoán cùng thống kê lỗi.

Kiểm thử API không tải model (chạy trong CI):
```cmd
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
```

Kiểm thử suy luận **thật** dùng chung một MP3, tải model nếu chưa được lưu cục bộ:
```cmd
python -m pip install -r requirements-asr.txt
python code\smoke_test_three_models.py
```
Kết quả thử một file được lưu tại `dataset/smoke_test_three_models.json`. Đây không phải đánh giá toàn bộ 1.000 mẫu. Không đưa kết quả của một câu vào báo cáo như độ chính xác trung bình.

## Đánh giá lại 1.000 audio bằng cả 3 model (không ghi đè CSV cũ)

Chạy trên máy đã kiểm thử thành công 3 mô hình. Từ thư mục `Vietnamese-ASR-Analyzer`:
```cmd
python code\evaluate_three_models_1000.py --limit 5
```

Chương trình sẽ ghi riêng vào `dataset/evaluation_recheck/`, hỗ trợ tiếp tục nếu tắt máy hoặc ngắt giữa chừng. **Để đánh giá đủ 1.000 file, phải dùng thư mục khác so với lần chạy thử 5 file**:
```cmd
python code\evaluate_three_models_1000.py --limit 1000 --output-dir dataset/evaluation_full_1000
```

Nếu chương trình báo lỗi mô hình, sửa nguyên nhân rồi chạy lại với `--retry-failed`; file đã chạy thành công sẽ không cần suy luận lại:
```cmd
python code\evaluate_three_models_1000.py --limit 1000 --output-dir dataset/evaluation_full_1000 --retry-failed
```

Khi cả ba file kết quả đã có **đúng 1.000 bản ghi thành công**, xuất báo cáo + bảng JSON + 2 biểu đồ SVG:
```cmd
python code\report_three_models_1000.py --input-dir dataset/evaluation_full_1000
```

Mở `dataset/evaluation_full_1000/REPORT.md`, `verified_comparison.json`, `chart_mean_wer.svg` và `chart_mean_cer.svg`. Nếu thiếu một bản ghi hoặc có lỗi, chương trình **không cho tạo báo cáo xác minh đầy đủ**. CSV lịch sử cho dashboard được giữ nguyên. Không đưa kết quả chạy thử 5 mẫu vào báo cáo chính thức. Khi chia sẻ, lưu kết quả đầu ra có nguồn gốc, thông tin checkpoint, câu chuẩn và lỗi thay vì chỉ chia sẻ số liệu tổng hợp.

## Triển khai Docker / Render

Có Dockerfile multi-stage (`Dockerfile`) build giao diện React và backend FastAPI
trong cùng image, đồng thời cài FFmpeg và cả ba engine nhận dạng tiếng nói.
Dịch vụ Render được mô tả ở `../render.yaml` (root repository).

**Không tự động tạo dịch vụ trả phí chỉ bằng git push.** Blueprint cần được
lập kế hoạch và người dùng xác nhận workspace, cấu hình chi phí trước khi áp dụng.
Chi tiết: [Hướng dẫn Render Docker](docs/RENDER_DOCKER.md).

Tại thư mục `Vietnamese-ASR-Analyzer`, chạy thử Docker:

```cmd
docker build -t vietnamese-asr-analyzer:local .
docker run --rm -p 10000:10000 vietnamese-asr-analyzer:local
```

Truy cập `http://localhost:10000`, `/health` và `/ready`.
Suy luận lần đầu tải checkpoint và có thể chậm; Docker build thành công
không đảm bảo cả ba mô hình đã thực sự được suy luận trên Render.
