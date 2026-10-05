# BÁO CÁO LAB 2 - ĐẶC TRƯNG TIẾNG NÓI VÀ NHẬN DẠNG BẰNG DTW

**Học phần:** CSE457 - Xử lý âm thanh và tiếng nói  
**Bài:** Lab 2 - Từ phân tích ngắn hạn đến MFCC, DTW và nhận dạng từ đơn

## 1. Mục tiêu

Xây dựng hệ nhận dạng 5 từ tiếng Việt tách rời theo pipeline: WAV → endpoint detection → framing/Hamming → MFCC → local distance → DTW → nearest-template → đánh giá.

## 2. Dữ liệu

Vocabulary: **không, một, hai, ba, bốn**. Mỗi từ có 5 utterance. Các file 01-03 là template training, 04-05 là test. Tổng 25 file.

Mọi file đều là WAV mono, PCM 16-bit, 16 kHz và có khoảng 0.2-0.5 s silence ở đầu/cuối. Tên đường dẫn dùng ASCII để tránh lỗi: `khong`, `mot`, `hai`, `ba`, `bon`.

**Lưu ý học thuật:** dataset đi kèm được tổng hợp bằng eSpeak để cung cấp project chạy hoàn chỉnh. Khi cần nộp dữ liệu cá nhân, thay bằng file tự thu và chạy lại toàn bộ pipeline.

## 3. Tham số baseline

| Tham số | Giá trị |
|---|---:|
| Sampling rate | 16000 Hz |
| Frame | 25 ms = 400 mẫu |
| Hop | 10 ms = 160 mẫu |
| Window | Hamming |
| Pre-emphasis | alpha=0.97 |
| NFFT | 512 |
| Mel filters | 24 |
| MFCC | 13 |
| Local distance | Euclidean |
| DTW normalization | Tổng cost / path length |
| Train/Test | 3/2 file mỗi lớp |

## 4. A - Thu dữ liệu và kiểm tra chất lượng

Các waveform của ba từ `không`, `một`, `hai` được lưu tại `figures/waveform_energy_zcr_3words.png`. Biên độ không clipping; silence đầu/cuối rõ ràng và đủ để ước lượng nền cho endpoint detection.

## 5. B - Đặc trưng miền thời gian

Mỗi file được chia frame 25 ms, hop 10 ms. Trên frame đã nhân Hamming tính:

- Energy: `E_r = sum(x_r[n]^2)`
- Magnitude: `M_r = sum(|x_r[n]|)`
- RMS: `sqrt(mean(x_r[n]^2))`
- Log-energy: `10 log10(E_r + eps)`
- ZCR: số lần đổi dấu trung bình trên một mẫu.

Silence có log-energy rất thấp. Voiced thường có energy cao và ZCR tương đối thấp; unvoiced/fricative có thể energy thấp hơn nhưng ZCR cao, vì vậy ZCR hữu ích khi tinh chỉnh biên.

## 6. C - Endpoint detection

Ngưỡng energy được ước lượng tương đối từ các frame silence đầu/cuối: `threshold = median(noise_log_energy) + 10 dB`. Sau khi tìm vùng active, thuật toán cho phép mở rộng tối đa 5 frame nhờ ZCR/energy thấp và cộng margin 50 ms hai phía để tránh cắt phụ âm.

File `endpoint_results.csv` ghi thời lượng trước/sau trim và biên start/end của toàn bộ 25 file. File ví dụ trim được lưu ở `trimmed_samples/khong_01_trimmed.wav`.

## 7. Autocorrelation và pitch

Trên frame có RMS lớn nhất của `khong_01`, đỉnh tự tương quan sau lag 0 cho ước lượng minh họa F0 khoảng **81.6 Hz**. Đây chỉ là phần minh họa tính tuần hoàn; pitch không được dùng làm feature chính của recognizer.

## 8. D - MFCC

Pipeline MFCC: pre-emphasis → frame/Hamming → FFT/power spectrum → 24 Mel filters → log → DCT → 13 MFCC. Sau đó áp dụng Cepstral Mean Normalization (CMN) theo từng utterance và dùng thống nhất cho train/test.

Mỗi frame luôn có 13 chiều MFCC nhưng số frame thay đổi theo thời lượng utterance. Vì vậy hai file nói cùng một từ có thể cho ma trận `(T1,13)` và `(T2,13)` với `T1 != T2`.

## 9. E - DTW tự cài đặt

Local distance: `d(i,j)=||x_i-y_j||_2`.

Dynamic programming dùng ba bước: ngang, dọc, chéo:

`D[i,j] = C[i,j] + min(D[i-1,j], D[i,j-1], D[i-1,j-1])`

Sau khi điền ma trận, backtracking từ ô cuối để thu optimal path. Cost được chuẩn hóa: `DTW_norm = total_cost / path_length`.

Kết quả ví dụ:

- Cùng từ (`mot_01` và `mot_04`): **15.867**
- Khác từ (`mot_01` và `bon_04`): **46.629**

Trong dataset hiện tại, chi phí cùng từ nhỏ hơn chi phí khác từ, đúng kỳ vọng của nearest-template matching.

## 10. F - Bộ nhận dạng nearest-template

Với mỗi test file: trim → MFCC → tính DTW đến 15 template → lấy khoảng cách nhỏ nhất theo từng nhãn → chọn nhãn có score nhỏ nhất. `results.csv` lưu nhãn thật, nhãn dự đoán và top-1/top-2/top-3 score cho 10 file test.

## 11. G - Đánh giá và thí nghiệm

Baseline accuracy trên dataset tổng hợp: **100.0%**.

| Thí nghiệm | Endpoint | Δ | Accuracy |
|---|---|---|---:|
| Baseline | Có | Không | 100.0% |
| E1_no_endpoint | Không | Không | 100.0% |
| E2_MFCC_delta | Có | Có | 100.0% |


Confusion matrix nằm tại `figures/confusion_matrix.png`.

**Nhận xét:** dữ liệu tổng hợp có điều kiện thu rất ổn định, nên accuracy có thể cao hơn đáng kể so với dữ liệu người thật. Khi thay dataset tự thu, cần đặc biệt kiểm tra endpoint, khoảng cách micro, tốc độ nói và biến thiên người nói.

## 12. Trả lời 9 câu hỏi báo cáo

### Câu 1. Vì sao không dùng toàn bộ waveform làm template chính khi hai utterance có thời lượng khác nhau?

Waveform là chuỗi mẫu rất nhạy với dịch thời gian, tốc độ nói, pha và biên độ. Hai lần nói cùng một từ thường có số mẫu khác nhau nên so sánh từng mẫu trực tiếp không phù hợp. MFCC nén thông tin phổ quan trọng theo frame và DTW cho phép căn chỉnh phi tuyến theo thời gian.

### Câu 2. Vai trò khác nhau của short-time energy và ZCR trong endpoint detection?

Energy giúp tách vùng có tiếng khỏi silence vì speech thường có năng lượng cao hơn nền. ZCR phản ánh tần suất đổi dấu; âm vô thanh/fricative có thể energy thấp nhưng ZCR cao. Do đó energy phù hợp xác định vùng speech thô, còn ZCR hỗ trợ giữ các phụ âm năng lượng thấp ở đầu/cuối.

### Câu 3. Vì sao Mel filterbank có khoảng cách theo Hz rộng dần khi tần số tăng?

Thang Mel mô phỏng độ phân giải cảm nhận của thính giác: ở tần số thấp con người phân biệt thay đổi tần số chi tiết hơn, còn ở tần số cao độ phân giải theo Hz thô hơn. Vì vậy các filter khi ánh xạ ngược về Hz sẽ rộng dần.

### Câu 4. Log trong MFCC có tác dụng gì? DCT biến M log-energy thành gì?

Log nén dynamic range và biến quan hệ nhân của phổ thành gần quan hệ cộng, phù hợp hơn với cảm nhận âm lượng. DCT biến M log-energy filterbank thành các hệ số cepstral, trong đó các hệ số thấp mô tả đường bao phổ tương đối trơn.

### Câu 5. Ý nghĩa bước ngang, dọc và chéo trong DTW?

Bước chéo ghép một frame X với một frame Y. Bước ngang lặp/giãn một frame của X so với nhiều frame của Y. Bước dọc làm điều ngược lại. Nhờ ba bước này, DTW bù được khác biệt tốc độ nói cục bộ.

### Câu 6. Vì sao phải chuẩn hóa DTW cost theo path length?

Nếu chỉ dùng tổng cost, utterance dài thường có nhiều cặp frame hơn và dễ nhận cost lớn chỉ vì độ dài. Chia cho path length tạo chi phí trung bình trên một bước căn chỉnh, giúp so sánh công bằng hơn giữa các utterance có thời lượng khác nhau.

### Câu 7. Ít nhất ba nguyên nhân làm cùng một từ có MFCC khác nhau giữa hai lần nói?

Tốc độ nói khác nhau; cao độ/cường độ khác nhau; khoảng cách/góc micro khác nhau; nhiễu môi trường; thay đổi phát âm và coarticulation; đặc tính kênh thu.

### Câu 8. Từ confusion matrix, chọn cặp từ dễ nhầm nhất và phân tích.

Trên dataset tổng hợp hiện tại, nếu confusion matrix không có lỗi thì không tồn tại cặp nhầm thực tế để kết luận. Điều này là giới hạn của dữ liệu tổng hợp sạch. Khi chạy với bản ghi thật, chọn ô ngoài đường chéo có số lượng lớn nhất rồi so sánh waveform, MFCC và DTW path của cặp đó để xác định nguyên nhân.

### Câu 9. Nếu muốn nhận dạng người nói mới chưa có template, DTW gặp hạn chế gì? Chương 3 giải quyết thế nào?

Nearest-template DTW phụ thuộc mạnh vào mẫu tham chiếu đã ghi. Với người nói mới, khác biệt giọng, cao độ và kênh thu có thể làm distance tăng và giảm độ chính xác. Theo phạm vi Lab, nội dung tiếp theo của Chương 3 chuyển sang mô hình thống kê/âm học như HMM để mô hình hóa biến thiên tốt hơn thay vì so trực tiếp với một số template cố định.

## 13. Kết luận

Project đã triển khai đầy đủ pipeline của Lab 2: đặc trưng thời gian, endpoint detection, autocorrelation, MFCC, DTW tự cài, recognizer nearest-template, confusion matrix và hai thí nghiệm bắt buộc E1-E2. Khi nộp chính thức bằng dữ liệu cá nhân, cần thay dataset tổng hợp bằng bản ghi thật và chạy lại notebook để cập nhật toàn bộ số liệu/đồ thị.
