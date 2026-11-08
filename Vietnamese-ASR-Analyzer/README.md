# Vietnamese ASR Analyzer

Ứng dụng FastAPI + React để nhận dạng audio mới và xem kết quả đánh giá tiếng Việt trên 1.000 mẫu Common Voice. Giao diện có ba lựa chọn: **OpenAI Whisper base**, **vinai/PhoWhisper-base** và **Wav2Vec2 Vietnamese**. Chọn model trên web trước khi xem thống kê hoặc gửi audio mới. Model chỉ tải khi nhận dạng audio mới; dashboard đọc kết quả đã lưu.

## Nguồn dữ liệu và kết quả

Các tệp `dataset/asr_results.csv`, `asr_results_phowhisper.csv`, `asr_results_wav2vec2.csv` được đồng bộ từ bản `ASR_Project(1).zip` do chủ dự án cung cấp. Mỗi tệp có 1.000 dự đoán, không có dòng lỗi; tên audio và câu chuẩn khớp 1.000 dòng trong `dataset/metadata.csv`. JSON phân tích câu, thống kê và so sánh được tạo lại từ các CSV này. Đây là kiểm tra tính nhất quán của kết quả đã lưu, **không phải lần chạy suy luận model mới trong GitHub**. Audio gốc (1.000 MP3 trong ZIP) không được đẩy vào repository, nên cần đặt tại `dataset/audio/` để phát lại và tái chạy đánh giá.

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
