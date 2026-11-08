# Triển khai Vietnamese ASR Analyzer lên Render bằng Docker

## Thiết kế

Một Render Web Service duy nhất phục vụ giao diện React đã build và FastAPI
trên cùng tên miền. Dữ liệu thống kê và 1.000 MP3 được đóng gói từ GitHub.
Ba checkpoint tải khi gọi nhận dạng lần đầu: Whisper base,
vinai/PhoWhisper-base và khanhld/wav2vec2-base-vietnamese-160h.

Không cần tạo Static Site thứ hai, cấu hình CORS tùy ý hoặc sửa giao diện đang dùng.
Trên máy Windows, `npm run dev` vẫn truy cập API địa phương cổng 8000.

## Cấu hình Render

- Repo: `https://github.com/vuvandat109/CSE457_Audio_Processing`
- Branch: `main`
- Blueprint: `render.yaml` ở thư mục gốc repo
- Dockerfile: `Vietnamese-ASR-Analyzer/Dockerfile`
- Docker context: `Vietnamese-ASR-Analyzer`
- Region: Singapore
- Web Service: `vietnamese-asr-analyzer`
- Health path: `/health`
- Gói dự kiến: `2c-4g` (2 CPU, 4 GB RAM; có phí). Người dùng phải xác nhận chi phí và workspace trước khi tạo.
- Biến `ASR_MAX_LOADED_MODELS=1` để hạn chế chiếm RAM, chỉ lưu một model trong bộ nhớ mỗi lần. Khi đổi model, hệ thống cần tải lại checkpoint từ bộ nhớ đĩa và có thể chậm.
- Không ghi đè, cập nhật hay chuyển các dịch vụ Gesture-AI hiện có.

Giá và cấu hình có thể thay đổi. Kiểm tra trang Render Pricing trước khi xác nhận.
Không dùng gói free 512 MB nếu cần suy luận thực cả ba model; nguy cơ hết RAM và restart cao.

## Chạy Docker tại máy có Docker

Từ gốc repository:

```powershell
cd E:\CSE457_Audio_Processing\Vietnamese-ASR-Analyzer
docker build -t vietnamese-asr-analyzer:local .
docker run --rm -p 10000:10000 --name vietnamese-asr-demo vietnamese-asr-analyzer:local
```

Truy cập `http://localhost:10000`, `http://localhost:10000/health`,
`http://localhost:10000/ready` và `http://localhost:10000/docs`.

Trên Render, hostname HTTPS được cấp sau khi triển khai thành công.
Không xem `/health` báo OK là bằng chứng cả ba model hoạt động; nó chỉ
kiểm tra web server. Cần kiểm thử upload thực qua giao diện.

## Kiểm thử khi triển khai

1. Trang chính hiển thị thống kê và phát được MP3 trong danh sách.
2. `/ready` trả về `status: ready` nếu dữ liệu cần thiết đầy đủ.
3. Chọn từng model, upload cùng MP3, nhập câu chuẩn và kiểm tra WER/CER.
4. Mở phân tích chi tiết âm vị, kiểm tra tiếng Việt, tải file và ghi âm
   trên trang HTTPS. Trình duyệt chỉ cho micro trên HTTPS hoặc localhost.
5. Kiểm tra Render Logs và mức RAM khi tải checkpoint, tránh suy luận đồng thời
   nhiều file nếu cấu hình máy nhỏ.

## Lưu ý vận hành

- Checkpoint AI không đóng sẵn trong image; lần suy luận đầu cần internet để
  tải từ OpenAI/Hugging Face. Không có bảo đảm thời gian nhận dạng.
- Cache checkpoint trên file system của Render có thể không tồn tại qua deploy/restart.
- Vì có ba model PyTorch, RAM và CPU là giới hạn chính. Bản miễn phí không
  phù hợp cho tất cả tính năng nhận dạng.
- Số liệu WER/CER cho 1.000 mẫu trong dashboard đến từ CSV đã lưu trước đó.
  Không nên nói đó là kết quả được chạy lại trên Render.
- Triển khai thành công nghĩa là cần kiểm chứng `/health`, `/ready` và
  thử nhận dạng thực. Chỉ có GitHub CI xanh chưa đủ xác nhận deploy.
