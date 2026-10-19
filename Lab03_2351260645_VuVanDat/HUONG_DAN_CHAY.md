# Lab 03 - Nhận dạng 5 lệnh tiếng Việt bằng Gaussian HMM

**Toàn bộ âm thanh kèm theo là GIỌNG TỔNG HỢP bằng eSpeak NG, không phải bản ghi người thật.** Đây là bộ thực nghiệm hoàn chỉnh để học và tái lập pipeline. Không trình bày dữ liệu này như dữ liệu tự thu; nếu giảng viên yêu cầu thu thật, thay WAV và chạy lại toàn bộ thí nghiệm.

## 1. Chạy nhanh (Windows / VS Code / terminal)

Giải nén ZIP, mở terminal tại thư mục `Lab03_HMM`:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python run_all.py
```

macOS/Linux: dùng `python3 -m venv .venv` và `source .venv/bin/activate`.
Python 3.12 đã được dùng để chạy kiểm chứng. Lần đầu có thể chậm do biên dịch JIT của librosa/numba. Không cần mạng, API key hay eSpeak để dùng WAV có sẵn và chạy Lab03.py.

Nhận dạng một file (đường dẫn tương đối từ thư mục đang mở):

```bash
python Lab03.py --predict dataset/test/mo/mo_01.wav
```

Kết quả gồm nhãn closed-set, nhãn sau reject, số frame và log-likelihood của 5 lớp. Log-likelihood **không phải phần trăm độ tin cậy**. Chỉ load pickle đáng tin cậy do chính bạn hoặc bộ bài này tạo.

## 2. Các tệp quan trọng

- `Bao_cao_Lab03.pdf`: báo cáo 6 trang, số liệu từ lần chạy thật trên dữ liệu tổng hợp.
- `run_all.py`: chạy lại thí nghiệm, ghi log và tạo báo cáo chỉ với một lệnh.
- `Lab03.py`: A-H, E1-E6, kiểm tra dữ liệu/topology/Forward/Viterbi, xuất toàn bộ kết quả.
- `generate_audio.py`: tái tạo WAV; cần cài eSpeak NG riêng và chạy `python generate_audio.py`.
- `dataset/`: train 60, val 20, test 20, test_noise15 20, unknown_val 4, unknown_test 4 =128 WAV, cộng1probe chẩn đoán dẫn xuất từ validation = **129 WAV**.
- `dataset/manifest.json`: thông số tổng hợp, nguồn gốc và SHA-256 từng file.
- `Nghe_thu_5_lenh.wav`: nghe theo thứ tự **mở - đóng - lên - xuống - dừng**; file nghe thử không đưa vào train/test.
- `models/hmm_5state_39d.pkl`: 5 model baseline đã huấn luyện.
- `results/summary.json`: kết quả đầy đủ; `results/run.log`: log lần chạy, có cả cảnh báo hội tụ.
- `results/figures/`: tất cả hình; `scores_test.csv`: likelihood cho **toàn bộ 20 test**, đáp ứng tối thiểu 3 mẫu.
- `results/training_*`: lịch sử EM, startprob, transmat và trạng thái kết thúc.
- `results/experiments.csv`, `dtw_vs_hmm.csv`, `sample_size.csv`, `lm_rerank.csv`, `lm_changes.csv`: bảng thí nghiệm.
- `lexicon.txt`, `corpus.txt`: dữ liệu **minh họa tự soạn**, chưa phải bộ chuẩn của giảng viên.
- `CAU_HOI_BAO_CAO.md`: câu trả lời đầy đủ 10 câu mục 6.1.
- `DOI_CHIEU_YEU_CAU.md`: ánh xạ yêu cầu đề sang tệp kiểm chứng.
- `build_report.py`: mã tạo lại báo cáo, chạy sau `Lab03.py` nếu đổi dữ liệu. Cần reportlab; font DejaVu từ matplotlib.

## 3. Quy trình và thiết kế

WAV mono PCM16/16kHz -> trim 30dB -> preemphasis 0.97 -> MFCC (13, 26 mel, FFT512, cửa sổ Hamming25ms, bước10ms) -> delta/delta2 (width tối đa9) -> CMVN từng utterance -> 5 whole-word HMM -> likelihood/argmax -> đánh giá.

CMVN tính riêng từng utterance, không trộn thống kê test vào train. Đây là xử lý offline toàn bộ utterance; không phải ASR streaming. Baseline cố định trước khi xem test: 5 state, diagonal covariance, 39 chiều. Khởi tạo Gaussian theo các đoạn thời gian đều nhau; cập nhật transition, means, covariance bằng Baum-Welch. π cố định ở state0; chuyển ngược/skip bằng0 và được assert sau fit. Không ép state cuối phải được ghé trước khi kết thúc utterance, tương ứng score() của hmmlearn và code đề.

E1 chọn số state bằng validation, ưu tiên ít state khi bằng điểm. **Không thay baseline 5 state theo kết quả test.** E2 so sánh13/39 chiều; E3 thử full có prior0.1I và covariance weight D+1 để hạn chế suy biến, do đó không phải full MLE hoàn toàn không regularization. E4 DTW dùng13MFCC, cùng split; Euclidean, bước(1,1)/(1,0)/(0,1), chọn đường tổng chi phí nhỏ nhất rồi chia độ dài đường, nearest template. Đây là baseline MFCC+DTW cài mới theo Lab2 vì chưa có code Lab2 của sinh viên. Có thêm HMM13 để quan sát ảnh hưởng feature. Timing loại trừ trích đặc trưng, lấy median3 lượt sau warmup, một thread; thời gian dựng template DTW không phải huấn luyện tham số. Tập con2/6/12 được lấy theo thứ tự tên file, không phải kết quả trung bình nhiều lần lấy mẫu.

E5 thêm nhiễu trắng15dB lên test; RMS tham chiếu lấy vùng tiếng nói trước khi padding0.3s. Dữ liệu noisy là dẫn xuất paired của test, không phải20 phép thử độc lập bổ sung. Các bản tổng hợp train/val/test có thông số speed/pitch/amplitude riêng; kiểm tra không trùng byte. Tuy nhiên cùng engine/voice và cùng cơ chế tổng hợp, nên **không chứng minh khả năng nhận dạng người nói mới**. Không dùng augmentation từ file train để tạo test.

## 4. Lexicon, LM và unknown

Lexicon dùng ký hiệu quy ước đơn giản, có token thanh điệu; đây không phải phiên âm chuẩn hoặc inventory giáo viên. Parser kiểm tra trùng từ và thiếu phone. Whole-word recognizer không dùng lexicon để fit. Khi nhận inventory chính thức, thay lexicon; nếu làm phone HMM, cần thêm dữ liệu/nhãn phone và nối model với quy tắc transition thích hợp.

Corpus là các chuỗi lệnh mô phỏng. Đếm unigram riêng và **outgoing-context counts** riêng. Bigram có add-k=0.5, vocabulary5 từ, không dự đoán EOS. Mẫu số là số lần context thực sự có từ kế tiếp + kV; không lấy nguyên unigram chứa cả vị trí cuối câu. Mỗi hàng xác suất tổng bằng1.

Re-ranking: `log P(X|word)/T + lambda * log P(word|previous)`. Thử0,0.1,0.3,1 và thêm3,10,30,100 để thấy LM lấn át acoustic. Tạo một probe từ validation bằng quét SNR10–50dB, chọn margin acoustic nhỏ nhất chỉ để minh họa re-ranking; loại probe khỏi accuracy và chọn threshold/model. Metadata nằm ở results/probe_metadata.json. Previous word được giả định để khảo sát độ nhạy; không được trình bày như context thực thu hay accuracy continuous speech. Nếu không quan sát sửa lỗi, ghi đúng là không quan sát, không sửa nhãn để tạo kết quả mong muốn.

Reject: threshold trên maximum log-likelihood/frame, chọn bằng balanced accuracy của known val20 và OOV val4 ("xin chào"). Đánh giá OOV test4 khác nội dung ("cảm ơn"); không dùng test để chọn threshold. Mẫu rất nhỏ và đều tổng hợp, chưa đủ để khẳng định detector unknown tổng quát. Có thể dùng thêm top1-top2 margin, nhưng phải hiệu chỉnh trên validation.

## 5. Cảnh báo hội tụ và giới hạn

`monitor_.converged` có thể đúng khi đạt giới hạn vòng lặp hoặc likelihood giảm. Vì vậy mã lưu `last_delta`, toàn bộ history và phân loại `tolerance`, `decrease`, `iteration_limit`, không coi mọi lần dừng là hội tụ tốt. Một vài delta âm nhỏ vẫn được giữ nguyên trong log/báo cáo. Không làm đẹp số liệu, không ép accuracy100%.

Test sạch chỉ20 mẫu; một mẫu thay đổi5 điểm phần trăm. Không suy diễn kết quả thành hiệu năng trên người dùng thật. Muốn đánh giá speaker-independent phải thu nhiều người và tách theo người; muốn chọn tham số ổn định cần validation đa dạng, nhiều seed/lần chia và kiểm tra ngoài engine TTS.

## 6. Thay dữ liệu thật

Giữ cấu trúc `dataset/{train,val,test}/{mo,dong,len,xuong,dung}/*.wav`, tách train/val/test trước khi xử lý. Sao lưu bộ synthetic vào thư mục khác; đừng trộn WAV thật vào manifest synthetic. Thu tối thiểu6train+2test/lớp/người theo đề; dành thêm validation nếu tuning. Cập nhật nguồn gốc trong manifest, tạo lại bộ noisy/OOV tương ứng, sửa counts và source trong summary/report cho dữ liệu thật, rồi chạy lại. Không dùng generator synthetic để thay thế âm thanh thật. Mã hiện tại và báo cáo được cấu hình rõ cho bộ129 WAV kèm theo.

## 7. Nguồn và tái lập

- Đề gốc: CSE457, Lab3, Đại học Thủy Lợi, file người dùng cung cấp (11 trang).
- hmmlearn API: https://hmmlearn.readthedocs.io/en/stable/api.html
- hmmlearn tutorial: https://hmmlearn.readthedocs.io/en/stable/tutorial.html
- eSpeak NG: https://github.com/espeak-ng/espeak-ng ; voice `vi`, version1.51.
- Generator dùng seed20261019; HMM random_state0, khởi tạo phân đoạn xác định.
- `requirements.txt` ghim phiên bản thư viện dùng thực tế. Thời gian chạy phụ thuộc máy; không cần giống số đo milliseconds để xác nhận thuật toán đúng.
