# Nguồn và giấy phép âm thanh

Các bản thu tiếng nói trong `clean/` và `separation/` là trích tuyển từ
**LibriSpeech ASR corpus, dev-clean**, do Vassil Panayotov, Guoguo Chen,
Daniel Povey và Sanjeev Khudanpur công bố qua OpenSLR SLR12.

- Nguồn: https://www.openslr.org/12/
- Kho tải: https://www.openslr.org/resources/12/dev-clean.tar.gz
- Giấy phép: [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/)
- Bài báo: “LibriSpeech: an ASR corpus based on public domain audio books”, ICASSP 2015.

`sources.csv` ghi đường dẫn gốc, mã người đọc, chương, thời lượng và cách chia tập.
Các đoạn gốc được đổi tên và chuyển FLAC sang PCM16 WAV mono 16 kHz. Hai nguồn ICA
lấy từ `spk01_test_01.wav` và `spk02_test_02.wav`. Các bản trong `results/audio/`
được biến đổi bằng đổi mức, cộng nhiễu, lọc, trộn hoặc tách. Khi chia sẻ lại, giữ
thông tin ghi công và mô tả biến đổi. Tác giả LibriSpeech không xác nhận kết quả bài làm.

`noise/fan.wav` là tín hiệu nhiễu quạt mô phỏng được sinh riêng cho bài thực hành.
