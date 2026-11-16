# Lab 5 với giọng đọc thật từ LibriSpeech

Mở hướng dẫn này khi chạy từng phần. Báo cáo chính ở `report.pdf`.

## 1. Giải nén và chạy trên Windows

1. Nhấp chuột phải vào `Lab5_LibriSpeech.zip` và chọn **Extract All**.
2. Trong VS Code, chọn **File → Open Folder**. Mở thư mục `Lab5` chứa
   `Lab5.py` và `requirements.txt`.
3. Chọn **Terminal → New Terminal**. Kiểm tra Python đã cài bằng `py -0p`.
4. Nếu danh sách có Python 3.12, chạy lần lượt các lệnh sau.

   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe Lab5.py
   ```

   Nếu danh sách có Python 3.11, đổi `-3.12` thành `-3.11`. Hai lệnh cuối
   gọi trực tiếp Python trong môi trường ảo nên không cần chạy lệnh kích hoạt.

5. Chờ dòng `Lab 5 complete. See results/ for WAV, PNG, CSV and JSON.`.
   Trong Explorer của VS Code, mở `results` để xem kết quả. Chạy lại cùng
   lệnh sẽ ghi lại các tệp cùng tên.

| Nếu gặp lỗi | Cách kiểm tra |
|---|---|
| `py` không được nhận diện | Kiểm tra `python --version`. Nếu có Python 3.11/3.12, dùng `python -m venv .venv`. Nếu cả hai lệnh đều lỗi, cài Python 3.11 hoặc 3.12 rồi mở lại Terminal. |
| Không tìm thấy `Lab5.py` | Chạy `Get-ChildItem`. Mở đúng thư mục chứa `Lab5.py` và `requirements.txt`. |
| `ModuleNotFoundError` | Chạy lại lệnh cài `requirements.txt` bằng `.\.venv\Scripts\python.exe`, rồi chạy bài bằng cùng Python đó. |
| CSV chỉ hiện trong một cột Excel | Vào **Data → From Text/CSV**, chọn dấu phân cách **Comma**. |

## 2. Dữ liệu đầu vào

`lab5_data/clean/` có 30 bản thu tiếng Anh từ ba người đọc trong LibriSpeech
dev-clean. `spk01`, `spk02` và `spk03` lần lượt là mã nguồn 652, 174 và 251.
Mỗi WAV dài 2–4 giây, mono PCM16 16 kHz. Mỗi người có 4 enrollment, 2 dev và
4 test. Enrollment lấy từ chương khác nhóm dev/test. Mỗi file nguồn chỉ xuất
hiện trong một tập. Hai nguồn ICA là bản sao của hai đoạn test khác người.
`lab5_data/sources.csv` ghi đường dẫn FLAC gốc để truy xuất từng đoạn.
Xem `lab5_data/ATTRIBUTION.md` để biết nguồn và giấy phép CC BY 4.0.

`noise/fan.wav` là nhiễu quạt mô phỏng. Sáu giây đầu dùng để tạo các ví dụ
nhiễu trên tập test. Hai giây cuối dùng ước lượng phổ nhiễu. Nhiễu ICA là
nhiễu trắng được đặt ở 25 dB tại từng microphone.

## 3. Khử nhiễu từng bước

1. Chuẩn hóa mức đoạn tham chiếu để có khoảng dự phòng biên độ. Tính công
   suất trung bình của đoạn nói và noise cùng độ dài. Nhân noise với
   α = √(P tiếng nói / (P noise × 10^(SNR/10))) rồi cộng vào đoạn nói.
2. Dùng cửa sổ Hann 25 ms, bước 10 ms và FFT 512 điểm. Trong mỗi ô thời gian
   và tần số, Spectral Subtraction trừ β lần PSD nhiễu và đặt giới hạn dưới
   γ lần PSD. Wiener ước lượng phần công suất của tiếng nói rồi dùng tỷ lệ
   công suất này để tính gain. Hai phương pháp giữ pha noisy.
3. Dùng iSTFT, cắt về đúng số mẫu của clean, rồi tính SNR trước và sau xử lý.
   Mở `results/enhancement.csv` để xem đủ 27 tổ hợp. Lọc β=1.5 và γ=0.01 để
   xem ba dòng cấu hình chuẩn như bảng sau.

| SNR đầu vào | SS đầu ra | Wiener đầu ra |
|---:|---:|---:|
| 0 dB | 5,35 dB | 5,54 dB |
| 5 dB | 9,11 dB | 9,20 dB |
| 10 dB | 13,13 dB | 13,22 dB |

Ở 5 dB, RMS sai số trong các khung yên giảm từ **0,0336**
xuống **0,0124** (SS) và **0,0120**
(Wiener). `enhancement_frame_diagnostics.csv` có cả sai số trên khung có tiếng
nói. So sánh hai vùng giúp phân biệt giảm nền và sai lệch tại vùng tiếng nói.
Ngưỡng vùng yên là ≤ 0,1% và vùng tiếng nói là ≥ 3% công suất của khung mạnh
nhất trong clean. Vùng ở giữa được bỏ qua.

### Kiểm tra toàn bộ 12 đoạn test

`enhancement_test_clips.csv` ghi SNR cho từng đoạn ở từng mức nhiễu và phương
pháp. Bảng sau lấy trung bình ΔSNR theo 12 đoạn, đơn vị dB.

| Mức nhiễu | Spectral Subtraction | Wiener |
|---|---:|---:|
| 0 dB | 6,07 | 6,27 |
| 5 dB | 5,03 | 5,18 |
| 10 dB | 4,14 | 4,25 |

### Nghe đối chiếu

Mở `results/audio/clean.wav`, `noisy.wav`, `enhanced_ss.wav` và
`enhanced_wiener.wav` liên tiếp, cùng âm lượng. Ba file xử lý ở đây dùng đầu
vào 5 dB. Mở `results/figures/spectrogram_5db.png` để đối chiếu cùng đoạn
trên một thang dB. Muốn nghe tác động của β, trong `results/audio/ablation/`
giữ floor 0.01 và chọn lần lượt beta 1, 1.5, 2. Muốn nghe tác động của γ,
giữ beta 1.5 và đổi floor 0, 0.01, 0.05.

| File | Tiếng ù ở khoảng nghỉ | Phụ âm và tiếng rít ngắn | Mốc giây |
|---|---|---|---|
| Noisy | … | … | … |
| Spectral Subtraction | … | … | … |
| Wiener | … | … | … |

Ghi điều nghe được trước khi xem bảng SNR để tránh lấy số đo làm thay cho
nhận xét bằng tai.

## 4. Đọc kết quả nhận dạng và xác minh

Tính MFCC theo từng khung. Lấy mean và std của MFCC cùng delta trên các khung
đủ năng lượng. Trung bình các vector enrollment theo từng người rồi chuẩn
hóa. Khi gặp đoạn test, lấy người có cosine cao nhất.

Ví dụ dòng đầu `speaker_scores.csv` cho `spk01_test_01.wav` có cosine với
`spk01`, `spk02`, `spk03` lần lượt 0,974,
0,929, 0,806. Nhãn dự đoán là
`spk01`. Test sạch đúng **8/12**. Trong hình
`confusion_matrix.png`, hàng là nhãn thật, cột là nhãn dự đoán.

| SNR đầu vào | Noisy | Spectral Subtraction | Wiener |
|---|---:|---:|---:|
| 0 dB | 4/12 | 4/12 | 4/12 |
| 5 dB | 4/12 | 8/12 | 8/12 |
| 10 dB | 8/12 | 8/12 | 8/12 |

Dùng `speaker_ablation.csv` để so sánh MFCC với MFCC+delta, bật/tắt CMN
và dùng 1, 2 hoặc 4 đoạn đăng ký. Thay một tham số mỗi lần. Khi accuracy
bằng nhau, xem `mean_margin`, tức điểm cosine với nhãn đúng trừ điểm
cao nhất trong hai nhãn còn lại rồi lấy trung bình.

**Xác minh** chỉ so đoạn nói với danh tính khai báo. Ngưỡng
0,918732 chọn trên dev theo |FAR − FRR| nhỏ
nhất và khóa trước khi chấm test. Trong `verification_trials.csv`,
`genuine=1` là khai đúng, `accepted=1` là hệ thống chấp nhận. Trên test có
24 lượt khai sai và 12 lượt khai đúng. FAR **41.7%**,
FRR **16.7%**. Đồ thị `far_frr.png` dùng các lượt dev.

## 5. Đọc kết quả FastICA

1. Nghe hai nguồn gốc A và B trong `lab5_data/separation/`.
2. Cắt hai đoạn cùng chiều dài, đặt cùng RMS, rồi tạo hai microphone theo
   ma trận trộn. Hai mic có tỷ lệ của mỗi giọng khác nhau.
3. Nghe `mix_mic1.wav`, `mix_mic2.wav` rồi nghe `separated_1.wav`,
   `separated_2.wav`. FastICA chỉ nhận hai mic. Chương trình dùng bản gốc
   sau khi tách để gán tên, chỉnh dấu và chấm điểm.
4. Xem `ica_correlation_before.png` và `ica_correlation_after.png`. Hàng
   là nguồn gốc và cột là đầu ra. Điểm đã ghép nằm trên đường chéo.
5. Đối chiếu `ica.csv`. Tương quan gần 1 nghĩa là dạng sóng gần nguồn gốc.
   SI-SDR đo mức sai lệch sau khi căn theo tỷ lệ biên độ tốt nhất.

| Ma trận | Nhiễu | Tương quan A | Tương quan B | SI-SDR A tách | SI-SDR B tách |
|---|---|---:|---:|---:|---:|
| Dễ | Không | 1,000 | 1,000 | 37,150 | 39,020 |
| Dễ | 25 dB | 0,995 | 0,996 | 19,950 | 21,174 |
| Gần suy biến | Không | 1,000 | 1,000 | 37,437 | 39,376 |
| Gần suy biến | 25 dB | 0,287 | 0,725 | -10,468 | 0,435 |

Đơn vị SI-SDR là dB. Các cột `mic1_a_si_sdr_db` và `mic2_b_si_sdr_db` là mức trước tách.

## 6. Hoàn thiện báo cáo và đưa lên GitHub

1. Điền họ tên, MSSV ở trang đầu báo cáo. Thêm nhận xét nghe A/B dựa trên
   các file ở mục 3 và 5. Nếu thay dữ liệu, cập nhật hình, bảng số liệu và
   câu trả lời có dẫn số liệu.
2. Nếu cần ảnh minh chứng, chụp ba màn hình theo thứ tự. Chụp Terminal có
   dòng hoàn tất, phổ suy giảm nhiễu ở 5 dB, rồi ma trận tương quan ICA sau
   ghép. Tên file và nhãn biểu đồ nên nhìn được trong ảnh.
3. Trên GitHub, mở repository đích. Chọn **Add file → Upload files**. Kéo
   nội dung đã giải nén trong thư mục `Lab5` vào trang tải lên.
4. Kiểm tra danh sách có `Lab5.py`, `requirements.txt`, `README.md`,
   `HUONG_DAN_CHI_TIET.md`, `report.pdf`, `lab5_data/` và `results/`.
   Chỉ đưa WAV của người thật lên nếu người thu đã đồng ý cho chia sẻ.
5. Nhập nội dung commit, ví dụ `Add Lab 5 audio processing`, rồi chọn
   **Commit changes**. Mở lại repository để kiểm tra các thư mục và file
   xuất hiện đúng vị trí.

Nếu đã clone repository về máy, hãy chép nội dung bài vào một thư mục con
`Lab5` ở repo. Mở Terminal tại gốc repo rồi chạy các lệnh sau.

```powershell
git status --short
git add -- Lab5
git diff --cached --stat
git commit -m "Add Lab 5 audio processing"
git push
```

Nếu bước xem danh sách staged hiện các tệp ngoài bài Lab 5, kiểm tra lại
trước khi commit. Nếu Git báo nhánh chưa có upstream, làm theo lệnh
`git push --set-upstream` mà Git in cho nhánh hiện tại.
