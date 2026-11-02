# Đối chiếu đề Lab 4

Đây là trạng thái thực tế của gói, không thay thế đánh giá của giảng viên.

| Yêu cầu | Trạng thái / bằng chứng |
|---|---|
| A: normalize_text miền hẹp | Có; Unicode, punctuation, digit-by-digit, giữ zero đầu, báo token lạ |
| A: >=15 unit, 2 candidate nếu có thể | Có 16 nhãn × 2 candidate × 2 giọng =64 WAV |
| A: mono 16k PCM16, RMS, metadata | Có; verification kiểm trực tiếp tất cả WAV |
| A: histogram duration/RMS | Hình 01 |
| B: raw_concat.wav | Có bản chuẩn nữ/câu 1 và 6 bản riêng theo câu/giọng |
| B: waveform/spectrogram và biên | Hình 02, 03, 09; boundaries.json |
| B: nhận xét nghe | Có hướng dẫn và điểm cần quan sát; chưa có người nghe chấm/chép lời |
| C: target + join trên 20-30 ms | Có; 25 ms, Hann, FFT512, log-spectrum MSE |
| C: DP chọn chuỗi tối ưu | Có; kết quả trùng vét cạn 2^9 đường, cả 2 giọng |
| C: cross-fade 0/5/15/30 ms | Có 24 WAV thí nghiệm (3 câu ×2 giọng ×4 mức), CSV |
| C: chọn giá trị dựa nghe/phổ | Có chọn 15 ms minh họa và phân tích phổ; cần người nghe để chốt lựa chọn chủ quan |
| C: best_concat + bảng cost 2 cách chọn | Có; fixed và DP cho 6 tổ hợp câu/giọng |
| D: đo F0 unit hữu thanh, Fs/Np | Có; pYIN + autocorrelation cục bộ; hình 08 |
| D: speed .8/1/1.2 và pitch -2/0/+2 | Có; phase-vocoder speed, WORLD pitch, hình 07 |
| D: giải thích source-filter | FORMULAS.md, QUESTIONS.md và báo cáo |
| E: state sequence, F0/spectral/duration | Có Gaussian HMM demo 5 state/word, frame10ms; NPZ/CSV |
| E: vẽ F0 và một spectral parameter | Hình 05; log-power1kHz, không giả là F1 |
| E: đổi duration/F0, nghe nếu resynthesis | Có WORLD resynthesis, 4 biến thể WAV |
| E: phân biệt waveform selection / generation | Có mô tả và code hai backend riêng |
| F: neural pretrained 3 câu offline | Có; 2 modelgiọng riêng, socket-block inference PASS |
| F: waveform/mel | Có WAV và 6 mel NPY tính từ waveform; không phải mel nội bộ model |
| F: latency cùng máy | Có 54 phép đo warm, model load ghi riêng |
| G: bảng backend, latency, bộ nhớ | Có số liệu khách quan trong báo cáo và CSV |
| G: intelligibility/naturalness/continuity thật | Chờ 5-10 người nghe; không tạo số MOS giả |
| 5.7: A/B hoặc MOS mini ít nhất 3 câu | Đã có phiếu nghe mù 26 clip, cần thu CSV thực tế |
| 7: trả lời 10 câu hỏi | QUESTIONS.md, báo cáo trang7-8 |
| 8: code chạy lại, audio, >=5hình | Lab04.py, 126 WAV (64 inventory +62 kết quả), 9 PNG |
| 8: báo cáo 5-8trang | PDF 8 trang, có script tạo lại |
| 8: ratings.csv nếu tổ chức nghe | Header trống + HTML thu CSV + script tổng hợp |

## Phạm vi chưa thể tự hoàn tất thay người nghe

1. Không có bản thu người thật: âm thanh được tạo bằng hai mô hình neural. Không ghi tên người thu, microphone hay phòng thu giả. Nếu yêu cầu môn học là tự ghi, cần thay bằng bản thu thật.
2. Không có người chấm thực tế: MOS/intelligibility/continuity chủ quan để pending. Điền số sau khi thu CSV. Không dùng proxy phổ để thay điểm con người.
3. Không đảm bảo âm thanh không có dấu vết AI. HMM và word concatenation là phương pháp học tập, có giới hạn nghe tự nhiên vốn có.

## Điểm rubric và nơi xem

Data/normalization1.0: data/, src/common.py. Baseline1.5: audio_output/, figures02. Selection/smoothing2.0: costCSV, figures04/09. Prosody1.0: experiments, figures07/08. HMM1.5: hmm_tts_backend.py, figure05. Neural1.0: ONNX offline, latency/mel. Evaluation/report2.0: PDF/QUESTIONS/FORMULAS; phần nghe thật cần hoàn tất.
