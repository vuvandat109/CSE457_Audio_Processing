# Đối chiếu đề Lab3

| Yêu cầu | Bằng chứng / tệp |
|---|---|
| A: WAV16k/mono/PCM16, MFCC39, CMVN | dataset_audit.csv; extract(); figures/features_mo.png, features_xuong.png |
| B: π và topology trái-phải | initialize(); asserts trong train(); training_log.json |
| C: lengths,5model, EM, lưu model | train(); models/hmm_5state_39d.pkl; convergence.png |
| D: score5model, ít nhất3test | scores_test.csv gồm20file ×5score; forward_viterbi_checks.json |
| D: ít nhất2Viterbi, duration | viterbi_mo.png; viterbi_xuong.png; state_durations.csv |
| E: DTW, accuracy/confusion/time/sample size | dtw_vs_hmm.csv; cm_dtw.png; sample_size.csv; disagreements.csv; dtw_path.png |
| F: lexicon/parser | lexicon.txt; lexicon_parser(); lexicon_parsed.json; bản minh họa chờ inventory giáo viên |
| G: unigram/bigram/add-k/re-ranking | corpus.txt; lm_counts.json; lm_rerank.csv; lm_changes.csv; lm_sensitivity.png |
| H: sạch/mismatch/score/unknown | scores_noise15.csv; cm_noise.png; score_distribution.png; reject_threshold.json |
| E1:3/5/7state | experiments.csv; training_3states.json, training_5states.json, training_7states.json |
| E2:13/39chiều | experiments.csv; scores_mfcc13.csv; cm_mfcc13.png |
| E3:diag/full | experiments.csv; scores_full_train.csv; scores_full_test.csv; training_full.json |
| E4:DTW/HMM | dtw_vs_hmm.csv |
| E5:mismatch | synthetic noise15dB; không gọi là speaker-independent |
| E6:lambda LM | 0/0.1/0.3/1 và3/10/30/100; context giả định |
| 10câu hỏi mục6.1 | CAU_HOI_BAO_CAO.md; trang6báo cáo |
| Báo cáo4-6trang | Bao_cao_Lab03.pdf (6trang) |
| README/cách chạy | README.md; requirements.txt |

Giới hạn cần công khai: giọng tổng hợp; corpus/lexicon tự soạn; baseline DTW được cài mới vì chưa có mã Lab2 của sinh viên. Đối chiếu lại các yêu cầu thu thật và inventory của giảng viên trước khi nộp chính thức.
