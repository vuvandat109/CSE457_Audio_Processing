# Lab 04 - Tổng hợp tiếng nói (CSE457)

**Mini TTS thông báo xếp hàng, hai giọng nam/nữ, ba backend chạy offline.**

Đã có sẵn dữ liệu, audio kết quả, biểu đồ, số liệu đo và báo cáo. Mở `audio_output` để nghe ngay; không cần cài Python để nghe các WAV đã tạo.

## Nguồn âm thanh và giới hạn cần trình bày đúng

- 64 unit được **tạo bằng neural Piper/VITS**, không phải thu microphone của người thật: 16 nhãn × 2 candidate × 2 giọng.
- Hai giọng thiết kế có sẵn: nam `diemdam`, nữ `altotram`; không mô phỏng danh tính một người cụ thể. Không tạo nữ bằng cách đơn thuần nâng pitch giọng nam.
- Mục tiêu là dễ nghe, nhưng **không đảm bảo không phân biệt được với giọng người**. Ghép từng từ và HMM demo thường còn rời rạc/robotic. Cần nghe kiểm tra nội dung trước khi nộp.
- Dữ liệu tổng hợp không thay thế được bằng chứng tự thu nếu giảng viên yêu cầu bản thu người thật. Muốn dùng người thật, thay các WAV cùng nhãn, rồi huấn luyện lại HMM và chạy lại pipeline.
- MOS/intelligibility chủ quan **chưa có người chấm**. `ratings.csv` chỉ có header, không có điểm giả. Có trang nghe mù và công cụ tính kết quả thật.
- HMM là demo Gaussian trái-sang-phải, 5 state/từ, học thống kê từ căn chỉnh chia đều; không phải HTS đầy đủ, không tuyên bố huấn luyện Baum-Welch.

## 1. Cấu trúc

```text
Lab04_TTS/
  Lab04.py                   # chạy toàn bộ thí nghiệm A-G khách quan
  neural_tts_backend.py      # inference ONNX thật, không gọi dịch vụ mạng
  hmm_tts_backend.py         # Gaussian states, static/delta generation, WORLD
  src/common.py              # normalization, cost, DP, cross-fade
  src/plots.py               # tạo 9 biểu đồ
  scripts/                   # dữ liệu, kiểm tra, báo cáo, đánh giá người nghe
  data/units/                # 64 WAV mono 16 kHz PCM16
  data/metadata.csv          # label, speaker, candidate, duration, RMS, source
  data/hmm_demo/             # 2 bộ tham số Gaussian HMM + mô tả
  models/                    # 8 phần model, 2 config, SHA-256 và model card
  audio_output/              # kết quả 3 câu x 2 giọng + các thí nghiệm
  figures/                   # 9 hình PNG
  results/                   # CSV cost/latency, tracks, mel, kiểm tra
  report/Bao_cao_Lab04.pdf   # báo cáo 8 trang
  FORMULAS.md                # công thức, ký hiệu, ví dụ tính toán
  QUESTIONS.md               # trả lời đủ 10 câu hỏi
  REQUIREMENTS_CHECKLIST.md  # đối chiếu từng yêu cầu
  listening_test.html        # phiếu nghe mù; mở bằng trình duyệt
  ratings.csv                # bảng trống chờ người nghe thực tế
```

## 2. Chạy lại trên Windows (khuyên dùng Python 3.12 64-bit)

Giải nén đầy đủ các gói vào cùng thư mục trước. Mở PowerShell trong `Lab04_TTS`:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe Lab04.py
.\.venv\Scripts\python.exe scripts\verify_submission.py
```

Hoặc nhấp đúp `CHAY_LAB04.bat`. Cài thư viện lần đầu cần Internet; **inference sau khi đã cài thư viện và có model không cần mạng**. Không tải model trong giờ Lab. Đã kiểm tra inference nam/nữ khi chặn kết nối socket trong `verify_submission.py`.

Nếu `py` không tồn tại, cài Python 3.12 64-bit và bật Add Python to PATH. Nếu dùng Linux, `pyworld` có thể cần trình biên dịch C++ (`g++`); Windows CPython 3.12 có wheel từ PyPI. Dùng Python 3.12 tránh lệch wheel/version. Thiếu `pkg_resources` được xử lý bằng phiên bản setuptools đã khóa.

Tạo câu mới trong miền hẹp:

```powershell
.\.venv\Scripts\python.exe Lab04.py --voice male --text "Mời khách hàng số 007 đến quầy 9."
```

Kết quả: `audio_output/custom_neural.wav`. Token không thuộc 16 nhãn sẽ báo lỗi rõ, không im lặng bỏ qua.

Các model được chia thành 4 phần/giọng, mỗi phần 16 MiB hoặc nhỏ hơn, để mỗi file dưới ngưỡng upload trình duyệt GitHub. Lần đầu chạy, wrapper ghép lại và kiểm SHA-256 **offline**. Các `.partXX` là dữ liệu model thật, không phải link tải hoặc file giữ chỗ. Giữ đủ các phần; không tự đổi tên chúng.

## 3. Dữ liệu và câu kiểm thử

1. Mời khách hàng số 23 đến quầy 5.
2. Mời khách hàng số 108 đến quầy 2.
3. Mời khách hàng số 479 đến quầy 6.

Số đọc từng chữ số: `23` -> `hai ba`, `108` -> `một không tám`. Không đọc thành số đếm. Tiền xử lý Unicode NFC, lowercase, dấu câu, khoảng trắng; giữ chữ số 0 đầu mã số.

Inventory gồm mời, khách, hàng, số, không-một-hai-ba-bốn-năm-sáu-bảy-tám-chín, đến, quầy. Mỗi giọng có 32 WAV, hai candidate có biến thiên tốc độ/noise của quá trình neural generation. Tất cả tên file không dấu để dễ dùng trên Windows/Git.

Tạo lại inventory (không cần làm để xem kết quả đã có):

```powershell
.\.venv\Scripts\python.exe scripts\prepare_inventory.py
```

Script giữ các file đã tồn tại. Muốn tái tạo ngẫu nhiên mới, sao lưu rồi xóa WAV cũ. Piper inference có tính ngẫu nhiên; số liệu chính xác của lần chạy nộp được lưu trong `results`. Không hứa waveform tái tạo từng bit.

Sau khi thay inventory người thật, xóa `data/hmm_demo/*_gaussian_hmm.npz`, chạy lại `Lab04.py`, rồi chạy `scripts/build_report.py` để cập nhật báo cáo. Metadata cần cập nhật theo file mới.

## 4. Thí nghiệm đã thực hiện

| TN | Thực hiện | Bằng chứng |
|---|---|---|
| Normalization/inventory | 16 nhãn, 2 candidate, 2 giọng | metadata, hình 01 |
| Baseline | Candidate 1, nối trực tiếp | `*_raw_concat.wav`, hình 02 |
| Candidate | 1 candidate cố định so với 2 candidate và DP | `unit_selection_costs.csv`, hình 04 |
| Cross-fade | 0, 5, 15, 30 ms; cùng chuỗi DP | `crossfade_metrics.csv`, WAV experiments, hình 09 |
| Speed | 0.8, 1.0, 1.2; phase vocoder librosa | `speed_*.wav`, hình 07 |
| Pitch | -2, 0, +2 semitone; WORLD giữ envelope/AP | `pitch_*.wav`, hình 07 |
| F0 | pYIN + kiểm tra chu kỳ tự tương quan | `f0_check.json`, hình 08 |
| HMM | 5 state/từ, Gaussian static/delta, WORLD | model NPZ, tracks/states CSV, hình 05 |
| HMM điều khiển | duration 0.8/1.2, F0 0.9/1.1 | 4 WAV trong experiments |
| Neural | 3 câu x 2 giọng, ONNX CPU offline | WAV, 6 mel NPY, môi trường/version |
| Latency | 3 lần warm/câu/giọng/backend | 54 dòng `latency.csv`; model load riêng |
| Người nghe | Đã chuẩn bị phiếu và script, CHƯA thu lượt nghe | `listening_test.html`, `ratings.csv` trống |

15 ms là cấu hình minh họa cân bằng, **chưa được kết luận tối ưu theo người nghe**. Spectral mismatch và bước nhảy một mẫu là proxy khách quan; không tương đương naturalness hoặc intelligibility. Hình 02 so sánh baseline và bản cải tiến tổng hợp; hình 09 giữ nguyên chuỗi candidate để tách ảnh hưởng cross-fade tại hai biên.

## 5. HMM generation có gì thật?

WORLD phân tích unit thành F0, spectral envelope và aperiodicity ở frame 10 ms. Chia mỗi từ thành 5 state có căn chỉnh giám sát. Ước lượng mean/variance static, delta, xác suất hữu thanh và self-loop từ hai candidate. Sinh state theo token và thời lượng kỳ vọng. Giải bài toán Gaussian static/delta bằng hệ ba đường chéo rồi WORLD tái tổng hợp waveform. Inference HMM không chọn lại waveform của unit.

HMM này dùng word-unit, ít dữ liệu, không có context-dependent phone clustering/HSMM và không thể đạt chất lượng HTS đã huấn luyện trên corpus lớn. Spectral track tại 1 kHz là log-power phổ, **không phải F1/formant được đo**. Training data của HMM và inventory cùng có nguồn neural: kết quả không phải một benchmark độc lập về ưu thế phổ quát của backend.

## 6. Thu điểm người nghe thật (phần cần bạn thực hiện)

1. Mở `listening_test.html` bằng Chrome/Edge sau khi giải nén; các WAV phải giữ nguyên cấu trúc tương đối.
2. Nhờ 5-10 người nghe bằng tai nghe; không cho xem key hoặc câu gốc trước khi chép lời.
3. Mỗi người nhập mã, nghe 26 clip (18 backend và 8 cross-fade), chép câu và chấm tự nhiên/liền mạch 1-5; tải CSV.
4. Gom các CSV vào một thư mục và tính kết quả, ví dụ:

```powershell
.\.venv\Scripts\python.exe scripts\evaluate_ratings.py ratings_L01.csv ratings_L02.csv
```

5. Kết quả ở `results/subjective_results.csv`. Đưa số liệu thật vào mục đánh giá của báo cáo. Báo cáo hiện ghi rõ đang chờ nghe thử; không có người nghe giả.

Key backend nằm trong `results/listening_key.csv`, chỉ người tổ chức dùng. Các đường dẫn WAV trong HTML có thể xem bằng công cụ trình duyệt, nên đây là che nhãn ở giao diện cho bài Lab, không phải bảo mật thí nghiệm. MOS chỉ là trung bình; không tự coi nhiều clip từ cùng một người là 18 người độc lập. Script tính thêm word accuracy từ edit distance có S/D/I; không gọi đó là exact sentence accuracy.

## 7. Đẩy lên GitHub không cần Git Bash

### Cách dễ nhất: GitHub Desktop

1. Giải nén gói đầy đủ, giữ thư mục `Lab04_TTS`.
2. Mở GitHub Desktop -> File -> New repository. Đặt tên, ví dụ `CSE457-Lab04-TTS`, chọn thư mục cha phù hợp.
3. Copy **nội dung bên trong** `Lab04_TTS` vào thư mục repository vừa tạo. Tránh tạo hai thư mục lồng nhau ngoài ý muốn.
4. Xem Changes: phải thấy `Lab04.py`, `data`, `models/*.partXX`, audio, report. Không thêm `.venv` hoặc ONNX đã ghép lại vì `.gitignore` đã loại chúng.
5. Điền Summary `Complete Lab 04 speech synthesis` -> Commit to main.
6. Publish repository, chọn quyền hiển thị theo yêu cầu môn học, rồi Publish.
7. Mở View on GitHub để kiểm tra source và báo cáo. Lưu URL để nộp.

### Nếu dùng Upload files trên website

Dùng các ZIP `GitHub_Phan_01...`, `02...`, `03...` đi kèm. Đây là **các gói ZIP độc lập**, không phải một ZIP bị chia bằng công cụ nén.

1. Giải nén từng phần vào **một thư mục riêng**, không trộn cả ba trước khi upload.
2. Ở ROOT repository -> Add file -> Upload files.
3. Kéo thư mục `Lab04_TTS` của phần 1 vào trang, chờ xong -> Commit changes.
4. Lặp lại ở ROOT repository với phần 2, rồi phần 3. Các file khác nhau sẽ bổ sung vào cùng thư mục `Lab04_TTS`.
5. Mỗi phần dưới 100 file; mỗi file model dưới 20 MB. **Không upload nguyên ZIP nếu cần hiển thị mã nguồn trực tiếp.**

Nếu trình duyệt không nhận kéo thư mục, dùng GitHub Desktop. Dung lượng tổng model khoảng 127 MB nên upload phần model có thể lâu. Không xóa model parts chỉ để upload nhanh: chúng cần thiết cho offline inference.

## 8. Tạo lại báo cáo và kiểm tra

```powershell
.\.venv\Scripts\python.exe scripts\build_report.py
.\.venv\Scripts\python.exe scripts\verify_submission.py
```

Báo cáo 8 trang được dựng từ số liệu CSV/JSON thực tế. Đọc `REQUIREMENTS_CHECKLIST.md` để xem phần đã làm và điều kiện còn cần người nghe/thu âm thật. Kiểm tra không chứng nhận âm thanh giống người 100%.

## Nguồn / phiên bản / giấy phép

- Đề Lab 4 CSE457 do người học cung cấp; tham chiếu Huang, Acero & Hon (2001), chương 14-16; Rabiner & Schafer (2010).
- Model: https://huggingface.co/vnhellboy/vietnamese-piper-voices ; revision `df2a53e0b5c8039d17e642cc8d80fa03d59374b7`. Model card gốc trong `models/MODEL_CARD.md`.
- Model card ghi license `other`, nêu lineage VAIS-1000 và Lessac/Blizzard research-only. Gói được chuẩn bị cho thực hành/nghiên cứu phi thương mại; không tuyên bố model mang MIT hoặc dùng thương mại tự do.
- Piper: https://github.com/OHF-Voice/piper1-gpl (GPL-3.0); cài từ PyPI, không đóng gói mã engine vào source bài làm.
- WORLD/PyWORLD: https://github.com/JeremyCCHsu/Python-Wrapper-for-World-Vocoder ; https://github.com/mmorise/World .
- librosa: https://librosa.org/doc/0.11.0/ .
- Các phiên bản thực sự chạy nằm trong `results/environment.json`; phần mềm khác có điều khoản riêng. Không gộp quyền model vào giấy phép của code bài Lab.
