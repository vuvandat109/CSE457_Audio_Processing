# Trả lời 10 câu hỏi mục6.1

1. **Forward và Viterbi:** Forward cộng xác suất tất cả đường trạng thái hợp lệ để tính P(X|λ). Viterbi lấy max và backtrack để tìm Q* làm P(X,Q|λ) lớn nhất. Trong miền log, phép cộng Forward trở thành logsumexp; Viterbi vẫn max. Log-prob Viterbi không đồng nhất với log-likelihood Forward. Bộ mã có cài riêng cả hai để kiểm chứng với thư viện trên2 utterance.

2. **γ và ξ:** γ_t(i)=P(q_t=i|X,λ) là trách nhiệm của state i với frame t. ξ_t(i,j)=P(q_t=i,q_(t+1)=j|X,λ) là trách nhiệm của cạnh i→j giữa hai frame. E-step dùng Forward–Backward để tính chúng; M-step cập nhật mean/covariance bằng trung bình có trọng sốγ, transition bằng tổngξ chia tổngγ ở các thời điểm có chuyển tiếp. Với nhiều utterance phải giữ ranh giới, không tạo chuyển từ cuối file này sang đầu file khác.

3. **Baum–Welch có thể hội tụ xấu:** EM tìm cực trị cục bộ, phụ thuộc khởi tạo. Những nguyên nhân thực nghiệm gồm: quá ít utterance/frame cho số state và số tham số; khởi tạo các state gần giống nhau hoặc phân đoạn không phù hợp; covariance nhỏ/suy biến; silence hoặc nhiễu chưa xử lý; mismatch train/test; lớp mất cân bằng. Giảm state, regularization, bổ sung dữ liệu và thử nhiều seed trên validation là các biện pháp hợp lý. Nhãn “converged” của thư viện không tự chứng minh nghiệm tốt; cần xem history và test độc lập.

4. **Diagonal covariance:** D=39 thì diag có39 phương sai/state, full có39×40/2=780 phần tử hiệp phương sai độc lập/state. Cộng39 mean:78 so với819 tham số phát xạ/state; với5state là390 so với4095. Full có thể mô tả tương quan nhưng cần nhiều dữ liệu, dễ singular/overfit; diag tiết kiệm và ổn định hơn. Số frame trong cùng utterance tương quan nên không tương đương từng ấy quan sát độc lập.

5. **Delta hữu ích:** A mô hình hóa chuyển trạng thái, trong khi phát xạ HMM chuẩn chỉ nhìn x_t ở state hiện tại. Δ và Δ² bổ sung xu hướng phổ trong vùng lân cận vào chính vector quan sát. Đây không phải bảo đảm luôn tăng accuracy; tăng chiều cũng tăng tham số và có thể làm kém hơn khi ít dữ liệu. CMVN từng utterance còn có thể làm mất một số thông tin tĩnh phân biệt.

6. **Khi nào cần lexicon:** Whole-word HMM ánh xạ trực tiếp mỗi từ sang một model, không cần lexicon để nhận5lệnh. Với hệ phone/subword muốn biểu diễn từ bằng chuỗi đơn vị phát âm, lexicon hoặc một cơ chế tương đương phải cung cấp ánh xạ. Ghép phone HMM theo thứ tự phát âm thành word HMM; cần xử lý transition ở ranh giới và các biến thể phát âm. Không phải mọi hệ ASR hiện đại đều bắt buộc dùng lexicon tường minh.

7. **Nói chậm:** Self-loop cho phép ở lại state nhiều frame, kéo dài duration mà không đổi thứ tự tiến triển. Trong state thông thường với a_ii<1, duration có dạng geometric; đây chỉ là mô hình duration đơn giản. Với terminal self-loop=1, việc dừng sequence do chiều dài quan sát quy định trong cấu hình này.

8. **Chia cho T:** Với cùng utterance, T là hằng số dương đối với mọi model nên argmax s_w và argmax s_w/T giống nhau. Score/frame hữu ích khi so utterance khác độ dài hoặc đặt reject threshold. Khi cộng LM, chia acoustic choT làm đổi thang tương đối, vì vậy phải hiệu chỉnh lambda theo đúng công thức đang dùng.

9. **DTW path và Viterbi path:** DTW đi trên lưới frame-test × frame-template để tối thiểu tổng khoảng cách cục bộ; alignment tham chiếu một mẫu cụ thể. Viterbi đi trên trellis thời gian × hidden-state để tối đa xác suất đường, kết hợp emission và transition học từ nhiều mẫu. Cả hai là dynamic programming nhưng mục tiêu và đối tượng căn chỉnh khác nhau. State không mặc nhiên là phoneme.

10. **Unknown:** Argmax trên5lớp luôn trả một lớp ngay cả khi tất cả model không phù hợp. Có thể reject nếu max(log-likelihood/T)<τ hoặc margin top1-top2 nhỏ. Chọnτ bằng validation có known và OOV, đánh giá false reject/false accept trên test riêng. Điểm log-likelihood không phải posterior được hiệu chỉnh, nên threshold phụ thuộc front-end, độ dài, môi trường và phân phối dữ liệu. Bộ bài dùng OOV val/test khác câu nhưng chỉ4mẫu mỗi tập nên chưa đủ cho ứng dụng thật.
