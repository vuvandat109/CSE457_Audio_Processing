# Triển khai Wav2Vec2 tiếng Việt với Render Free và Docker

## Kiến trúc

Một Docker image chứa React frontend đã build và FastAPI. Trong backend chỉ
có **Wav2Vec2 tiếng Việt** (checkpoint `khanhld/wav2vec2-base-vietnamese-160h`).
Docker image chứa 1.000 MP3 và toàn bộ thống kê Wav2Vec2 đã lưu.

Ứng dụng dùng cùng domain, tránh phải trả phí cho frontend/backend riêng.

## Tài nguyên miễn phí

Blueprint ở `../render.yaml` sử dụng `plan: free` tại Singapore.
Render Free giới hạn khoảng 512 MB RAM và cho máy ngủ khi không dùng.
**Không thể đảm bảo PyTorch và Wav2Vec2 hoạt động trong 512 MB RAM.**
Đây là bản thử, chưa có xác nhận suy luận model thành công trên Render Free.
Không bật gói trả phí nếu chủ dự án chưa đồng ý.

## Docker chạy cục bộ

```cmd
cd /d E:\CSE457_Audio_Processing\Vietnamese-ASR-Analyzer
docker build -t vietnamese-asr-wav2vec2:local .
docker run --rm -p 10000:10000 --name wav2vec2-asr vietnamese-asr-wav2vec2:local
```

Mở:
- `http://127.0.0.1:10000` để xem giao diện.
- `http://127.0.0.1:10000/health` để kiểm tra HTTP server.
- `http://127.0.0.1:10000/ready` để kiểm tra dữ liệu.
- `http://127.0.0.1:10000/docs` để xem FastAPI.

Đăng nhập Render, kết nối GitHub `vuvandat109/CSE457_Audio_Processing`,
chọn Blueprint `render.yaml`, kiểm tra mọi tài nguyên đều thuộc gói Free và
xác nhận trước khi triển khai. Không tác động các dịch vụ Gesture-AI khác.

## Kiểm tra cuối sau deploy

1. Website mở được, biểu đồ WER/CER từ 1.000 mẫu hiển thị.
2. Phát MP3 trong danh sách và mở phân tích từ/âm vị.
3. Upload MP3 và chạy nhận dạng bằng Wav2Vec2 thật.
4. Nhập câu chuẩn, đối chiếu từ sai, WER và CER.
5. Xem Render Logs để xác nhận tải checkpoint thành công hoặc lỗi thiếu RAM.
6. Ghi âm bằng microphone qua HTTPS.

`/health` thành công **không chứng minh Wav2Vec2 chạy được**.
Trọng số tải khi nhận dạng lần đầu và có thể bị mất khi free instance ngủ,
restart hoặc deploy. Kết quả 1.000 mẫu hiển thị là CSV trước đó, không
phải suy luận lại trên Render.

Nếu Render Free báo hết RAM, giải pháp miễn phí khả thi hơn là giữ model
trên máy Windows và công khai qua Cloudflare Tunnel. 
