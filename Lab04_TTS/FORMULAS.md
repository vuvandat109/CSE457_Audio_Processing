# Công thức Lab 4: ký hiệu, cách dùng và ví dụ

Các ví dụ ghi rõ "minh họa" không phải số liệu đo. Số liệu thực tế ở `results/*.csv` và `f0_check.json`.

## A. Văn bản và mức tín hiệu

`T -> normalize -> W -> lexicon/unit lookup -> units`. T là văn bản; W là token chuẩn hóa. Mã 023 được đọc không-hai-ba. Cùng một số có thể cần đọc khác nếu ngữ cảnh không phải mã hàng đợi.

**Duration:** d=N/Fs. N là số mẫu, Fs mẫu/giây. Ví dụ N=4800, Fs=16000 -> d=0.3 s.

**RMS:** R=sqrt((1/N) sum_n x[n]^2). Chuẩn hóa y[n]=g*x[n], g=R_target/R. Triển khai giới hạn gain để peak không vượt 0.97, thay vì tăng rồi hard-clip làm méo. RMS mục tiêu 0.08; nếu peak-limit hoạt động thì RMS có thể thấp hơn 0.08.

## B. Hàm chi phí và quy hoạch động

**Target:** Ct(j,k)=((d_jk-d_ref,j)/0.05)^2 + ((R_jk-0.08)/0.02)^2.

- d_ref,j là duration candidate 1 của cùng từ, một mục tiêu chuẩn trong demo.
- 0.05 s và 0.02 là thang chuẩn hóa tự chọn, không tuyên bố là phương sai đo được.
- Cần cân nhắc normalization RMS làm thành phần RMS rất nhỏ; duration vẫn tạo trade-off.

Ví dụ minh họa d=0.35, d_ref=0.30, R=0.09 -> Ct=(0.05/0.05)^2+(0.01/0.02)^2=1.25.

**Join feature chuẩn hóa trong đề:** Ck=(f_end,k-f_start,k)^2/sigma_k^2. Ví dụ F0 150 và 170 Hz, sigma=20 Hz -> Ck=1. Không so sánh F0 khi một đầu vô thanh mà coi F0=0 là pitch thật.

**Join được triển khai:** lấy 25 ms (400 mẫu) ở hai đầu, nhân Hann; FFT 512 -> 257 bin không âm. L=20*log10(max(abs(FFT),1e-8)); Cj=mean_k((Lleft-Lright)^2), đơn vị dB². FFT 512 có zero-padding; không làm độ phân giải vật lý của cửa sổ 25 ms tốt hơn một cách kỳ diệu.

Ví dụ minh họa Lleft=[-20,-30,-40], Lright=[-22,-29,-35] -> Cj=(4+1+25)/3=10 dB².

**Tổng:** C=sum_j Ct(j,kj)+lambda*sum_j Cj(kj,kj+1), lambda=0.02. Join có thang dB² nên cần trọng số để không lấn át tùy ý. Không diễn giải tổng cost là điểm nghe 1-5.

**DP:** D1(k)=Ct(1,k); Dj(k)=Ct(j,k)+min_i[D(j-1,i)+lambda*Cj(i,k)]. Lưu argmin ở mỗi bước, bắt đầu truy vết từ state cuối có D nhỏ nhất. Với J token, M candidate/token, độ phức tạp O(J*M²), so với O(M^J) nếu vét cạn. Script verification đối chiếu DP với đủ 2^9 đường cho câu 1 ở cả hai giọng.

## C. Cross-fade và overlap-add

N=round(Fs*t_ms/1000). Ở 16 kHz: 5/15/30 ms -> 80/240/480 mẫu.

alpha[n]=n/(N-1), n=0..N-1; y_overlap[n]=(1-alpha[n])*a_tail[n]+alpha[n]*b_head[n]. Sau đó nối a trước overlap, vùng overlap, b sau overlap. N=0 dùng nối trực tiếp.

Ví dụ minh họa alpha=.25, a=.8, b=.4 -> y=.75*.8+.25*.4=.7. Đây là trung bình có trọng số tại một mẫu, không phải dịch cao độ.

Nout=sum_j Nj-(J-1)*N khi mọi unit đủ dài. Chín unit với overlap 15 ms làm câu ngắn hơn tổng duration 8*.015=.12 s. Phải tính lại vị trí biên sau mỗi lần overlap.

OLA tổng quát: y[n]=sum_r x_r[n-rR]. Nếu khung phân tích/tổng hợp dùng các cửa sổ có tổng chồng lấn bằng hằng số phù hợp, có thể tái tạo tín hiệu gốc với chuẩn hóa tương ứng. Cross-fade hai đoạn khác nhau không đảm bảo không còn mọi khác biệt spectral/phase.

## D. F0, thời lượng, semitone và source-filter

F0=Fs/Np; Np mẫu/chu kỳ. Kết quả đo cụ thể ở f0_check.json. Kiểm tra tự tương quan được tìm quanh chu kỳ pYIN dự đoán; không gọi đây là hai phép đo ground truth độc lập.

Speed r: Tout=Tin/r. Tin=2 s -> r=.8 cho 2.5 s, r=1.2 cho 1.6667 s. Duration scale alpha: Tout=alpha*Tin; hai quy ước ngược nhau.

Pitch ratio r=2^(delta_s/12); F0new=r*F0old. Với F0old=160 Hz: -2 st ->142.54 Hz; +2 st ->179.59 Hz. Cùng một waveform có voiced/unvoiced, không được gán F0 cho toàn bộ vùng vô thanh.

Source-filter: X(z)=E(z)*H(z), H(z)=(b0+sum bk*z^-k)/(1-sum ak*z^-k). z^-k là trễ k mẫu; E là nguồn rung/nhiễu, H là bộ lọc cộng hưởng. F0 và formant là hai loại đại lượng khác nhau. Trong TN pitch, WORLD giữ sp/ap, đổi f0, giúp tách nguồn khỏi spectral envelope. Vẫn có thể có lỗi phân tích và artifact vocoder.

PSOLA (lý thuyết trong câu hỏi): x_i[m]=w_i[m]*x[ta_i+m]; y[n]=sum_j y_j[n-ts_j]. Khoảng ts[j+1]-ts[j] giảm -> chu kỳ giảm -> F0 tăng. Đổi số lượng/chọn lặp đoạn có thể đổi duration. Thí nghiệm thực tế của gói dùng phase-vocoder cho speed và WORLD cho pitch, không gắn nhãn nhầm là đã cài TD-PSOLA/WSOLA.

## E. Gaussian HMM generation

lambda=(A,B,pi). A là chuyển state; B là Gaussian phát xạ acoustic vector; pi bắt đầu ở state đầu của từ đầu. Mỗi word có 5 state trái-sang-phải, chỉ self-loop hoặc đi state sau, state cuối chuyển sang từ kế tiếp do text xác định.

State duration mean dbar frames; a_ss=1-1/dbar. Phân bố dwell time geometric có kỳ vọng 1/(1-a_ss)=dbar. Demo dùng duration kỳ vọng làm tròn, không tuyên bố đó là duration mode (mode geometric thường là 1). Có ràng buộc phải đi đủ 5 state.

Vector c=[continuous logF0, log spectral envelope bins, aperiodicity bins]. Xác suất voiced được ước lượng riêng; chỉ xuất F0>0 khi voiced_prob>=.5. Ở 16 kHz, WORLD tự chọn FFT phù hợp; số bin lưu trong NPZ, không hard-code 257 như join-cost FFT.

Gaussian: p(c|s)=prod_k [1/sqrt(2*pi*v_sk)]*exp(-(c_k-mu_sk)^2/(2*v_sk)). Mean/variance tính từ 2 candidate với căn chỉnh chia đều; variance floor 1e-3. Dữ liệu rất ít nên variance không đại diện corpus lớn.

Dynamic feature được dùng nhất quán là sai phân lùi: (D c)_t=c_t-c_(t-1), t>=1. Đây là lựa chọn đơn giản thay cho delta đối xứng thông dụng; train và generation dùng cùng toán tử.

Minimize J(c)=sum_t (c_t-mu_t)^2/v_t + sum_(t>=1) ((c_t-c_(t-1))-mu_delta,t)^2/v_delta,t.

Gradient bằng 0 -> [diag(1/v)+D.T*diag(1/v_delta)*D] c = mu/v + D.T*(mu_delta/v_delta). Ma trận ba đường chéo; scipy.linalg.solve_banded giải theo từng chiều. Tương đương nghiệm maximum-likelihood Gaussian static/delta trong cấu hình demo này. Delta có mean/variance học được, không chỉ lọc trung bình đường vẽ.

Ví dụ minh họa mu=[500,700,900], static variance=1, delta mean=0, delta variance=1: J=(c1-500)^2+(c2-700)^2+(c3-900)^2+(c2-c1)^2+(c3-c2)^2. Hệ: 2c1-c2=500; -c1+3c2-c3=700; -c2+2c3=900 -> c=[600,700,800]. Độ thay đổi mỗi bước từ 200 xuống 100. Mean delta khác 0 thì nghiệm còn cố giữ xu hướng mong muốn.

Cuối cùng WORLD tổng hợp từ f0, sp, ap. Thay duration bằng tăng/giảm số frame state; thay F0 bằng nhân hệ số .9/1.1 trên các frame voiced. Không thay toàn bộ vocal-tract filter theo pitch.

## F-G. Thời gian và đánh giá

Latency=t_end-t_start. Trong bài đo warm, không tính tải model và I/O WAV; normalization, generation, resampling/RMS đều nằm trong phạm vi. Model load được ghi riêng. 3 lần/câu x3 câu x2 giọng x3 backend =54 phép đo.

RTF=latency/audio_duration. RTF<1 nghĩa sinh nhanh hơn thời lượng phát, không chứng minh chất lượng tốt hơn.

MOS=(1/K)*sum_i rating_i, rating_i=1..5. Ví dụ minh họa [4,3,4,5,4] ->4.0. Không có dữ liệu thật thì để pending, không điền ví dụ vào bảng kết quả.

Đề: intelligibility=100*N_correct/N_total; phải xác định đơn vị từ hay câu. Script chép lời dùng edit distance để tính word accuracy=100*(1-(S+D+I)/N), xử lý cả thay thế, xóa, chèn; khác chỉ số exact-match câu. MOS và intelligibility không suy ra từ spectral MSE.
