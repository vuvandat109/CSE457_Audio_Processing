# Vietnamese ASR Analyzer

Dự án đánh giá nhận dạng tiếng Việt bằng **OpenAI Whisper base**, tính WER/CER, phân tích lỗi âm tiết và trình bày kết quả bằng FastAPI + React. Dashboard đọc **kết quả đã lưu** trong `dataset/`; chạy dashboard không tải model và không cần các MP3 gốc. Chạy đánh giá mới cần audio Common Voice, FFmpeg và tải model Whisper ở lần chạy đầu.

## Kết quả hiện có

Bộ kết quả lưu trong repo gồm **20 mẫu** lấy từ 20 dòng đầu của `dataset/metadata.csv`: WER trung bình theo câu **41,18%**, CER trung bình theo câu **16,99%**; 19 câu có lỗi và 1 câu đúng theo bộ phân tích hiện tại. Đây là thử nghiệm sơ bộ, không phải độ chính xác trên toàn bộ Common Voice. Không dùng những số này để suy ra hiệu năng chung hoặc so sánh các model khác nhau.

$$
\mathrm{WER}=\frac{S+D+I}{N_{\mathrm{từ\ chuẩn}}}, \qquad
\mathrm{CER}=\frac{S_c+D_c+I_c}{N_{\mathrm{ký\ tự\ chuẩn}}}.
$$

`S`, `D`, `I` lần lượt là thay thế, bỏ sót và thêm. WER/CER trung bình trên dashboard là trung bình các tỷ lệ **từng câu**; `corpus_wer` là tỷ lệ gộp theo tổng số từ. Các bước chuẩn hóa, tách từ và xử lý dấu câu ảnh hưởng đến điểm số.

## Cấu trúc

- `code/`: chuẩn bị dữ liệu, Whisper batch inference, WER/CER, phân tích lỗi, tạo JSON thống kê.
- `dataset/metadata.csv`: danh sách khoảng 1.000 tên clip và transcript; `dataset/asr_results.csv`: 20 dự đoán lưu sẵn.
- `dataset/sentence_analysis.json`, `error_statistics.json`, `summary_report.json`: dữ liệu cho dashboard/báo cáo.
- `dataset/audio/`: để trống khi clone; MP3 Common Voice không được đẩy lên GitHub.
- `web/backend/`: FastAPI đọc JSON; `web/frontend/`: React/Vite.
- `tests/`: kiểm tra phép tính và API không cần audio gốc.

## Chạy dashboard từ GitHub

Yêu cầu Python **3.12**, Node.js **22+**, npm. Mở terminal ở thư mục `Vietnamese-ASR-Analyzer`:

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux/macOS:
# source .venv/bin/activate
python -m pip install -r requirements.txt
cd web/backend
python -m uvicorn main:app --reload
```

Mở terminal thứ hai từ gốc dự án:

```bash
cd web/frontend
npm ci
npm run dev
```

Truy cập http://localhost:5173; API http://127.0.0.1:8000/docs. Danh sách, biểu đồ, WER/CER và chi tiết câu hoạt động từ dữ liệu lưu sẵn. Nút phát audio chỉ có tác dụng sau khi bạn đặt đúng MP3 vào `dataset/audio/`. Nếu muốn dùng frontend khác cổng/API, đặt `VITE_API_URL` trước khi chạy Vite và cấu hình `CORS_ORIGINS` cho backend.

## Chạy lại Whisper trên audio thật

Tải Common Voice tiếng Việt từ Mozilla theo điều kiện cấp phép của bộ dữ liệu. Giải nén `validated.tsv` và thư mục `clips/`. Cài **FFmpeg** và xác nhận `ffmpeg -version` chạy trong terminal. Audio gốc không có trong repo; không thể kiểm chứng lại đầu ra Whisper chỉ bằng mã nguồn và CSV.

Nếu muốn tạo lại metadata và chép tối đa 1.000 clip từ tập gốc:

```bash
python code/prepare_data.py --tsv "/duong-dan/vi/validated.tsv" --clips "/duong-dan/vi/clips" --limit 1000 --seed 42
```

Trên Windows thay đường dẫn bằng đường dẫn thật, ví dụ `C:\...\validated.tsv` và `C:\...\clips`. Nếu muốn tái hiện đúng bộ 20 mẫu lưu sẵn, lấy đúng 20 tên MP3 đầu trong `dataset/metadata.csv` và chép vào `dataset/audio/` (không cần tạo lại metadata).

Cài thêm model inference và đánh giá:

```bash
python -m pip install -r requirements-whisper.txt
python code/batch_evaluate.py --limit 20 --model base
python code/generate_sentence_analysis.py
python code/generate_error_statistics.py
```

`batch_evaluate.py` mặc định chọn 20 dòng đầu để đối chiếu với bộ kết quả đang lưu; chạy `--sample --limit 100 --seed 42` để làm thí nghiệm ngẫu nhiên mới, hoặc `--limit 0` để đánh giá toàn bộ metadata. Các lệnh ghi đè kết quả trong `dataset/`; sao lưu trước nếu cần giữ mốc 20 mẫu. Model Whisper tải từ mạng ở lần chạy đầu, không có trong Git. Các script phân tích cũ (`analyze_errors.py`, `analyze_vietnamese_errors.py`, `confusion_analysis.py`, `generate_report.py`) có thể chạy thêm sau batch evaluation; phần web hiện dùng `sentence_analysis.json` và `error_statistics.json`.

## Kiểm thử

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
cd web/frontend
npm ci
npm run lint
npm run build
```

GitHub Actions chạy các kiểm tra trên khi thư mục dự án thay đổi. Test không gọi Whisper và không tải MP3. Mã tách âm tiết dựa trên luật/từ điển nên các nhãn lỗi âm đầu, âm chính, âm cuối và thanh điệu là phân tích gần đúng; cần đối chiếu thủ công trước khi dùng làm kết luận ngôn ngữ học.

## Tác giả

Vũ Văn Đạt · CSE457 Audio Processing.
