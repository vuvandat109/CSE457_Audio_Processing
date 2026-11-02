# Trả lời 10 câu hỏi báo cáo Lab 4

## 1. Vì sao ghép các đoạn tự nhiên vẫn kém tự nhiên?

Tính tự nhiên của một đoạn không đảm bảo tính liên tục khi đặt cạnh đoạn khác. Hai từ có thể khác pitch, energy, spectral envelope, pha và ngữ cảnh phát âm. Coarticulation và ngữ điệu toàn câu cũng thiếu. Cross-fade chủ yếu xử lý vùng biên, không tự tạo được ngữ điệu hoặc đồng phát âm đúng. Trong gói này unit còn là neural-generated, cần ghi đúng nguồn thay vì gọi là bản thu người thật.

## 2. Target cost khác join cost? Chỉ tối ưu join có vấn đề gì?

Target cost đo candidate có hợp duration/RMS/context mong muốn; join cost đo tương thích cuối-trước/đầu-sau. Chỉ tối ưu join có thể chọn từ có duration/ngữ điệu sai mục tiêu hoặc chọn vùng năng lượng quá thấp chỉ vì phổ hai đầu giống nhau. Tổng cost có trọng số và quy hoạch động tìm đường toàn cục. Bài dùng duration candidate 1 làm mục tiêu và RMS .08, trọng số join .02.

## 3. Vì sao cross-fade quá dài làm mờ phụ âm?

Phụ âm bật/tắc và chuyển tiếp nhanh chứa thông tin ngắn. Overlap quá dài pha trộn chúng với âm cạnh bên, giảm độ sắc nét của burst, che phụ âm yếu và rút ngắn nhịp. 30 ms không mặc nhiên tốt hơn 5/15 ms; cần nghe và xem hai biên với cùng candidate để tránh nhiễu do thay cả unit selection.

## 4. Vì sao đổi F0 không đồng nghĩa đổi formant?

X=E*H: nguồn E quyết định nhịp rung cơ bản, đường thanh H quyết định cộng hưởng. F0 là khoảng cách harmonic, formant là vùng cộng hưởng của spectral envelope. Có thể giữ cùng nguyên âm trong khi hát các nốt khác. Đổi sample rate phát đơn thuần dịch cả hai và cả duration; WORLD/PSOLA phù hợp hơn để tách điều khiển, nhưng còn giới hạn phân tích.

## 5. PSOLA thay pitch và vì sao voiced fricative kéo dài bị buzziness?

PSOLA lấy các đoạn có cửa sổ quanh pitch epoch, đặt vào synthesis epoch và cộng chồng. Khoảng epoch nhỏ hơn -> F0 cao hơn; lớn hơn -> F0 thấp hơn. Lặp/drop đoạn giúp đổi duration. Voiced fricative có cả rung tuần hoàn và nhiễu xát; lặp nguyên đoạn nhiễu theo nhịp đều tạo tuần hoàn giả, làm nghe rè/buzzy. Epoch sai còn gây sai pha. TN của gói thực tế dùng WORLD/phase-vocoder, không giả nhận đã chạy PSOLA.

## 6. Vì sao thêm delta làm trajectory HMM trơn hơn?

Nếu tối ưu từng frame theo mean state độc lập thì giá trị thường nhảy tại ranh giới. Ràng buộc delta liên kết frame lân cận và phạt thay đổi không phù hợp với phân bố động. Generation phải giải đồng thời static và delta, không chỉ bổ sung cột rồi vẽ lại. Mức trơn phụ thuộc variance, delta mean và giới hạn voiced/unvoiced; không phải mọi ranh giới đều nên bị làm phẳng.

## 7. Vì sao waveform concatenation cần inventory lớn?

Cùng một đơn vị có nhiều hiện thực theo âm trước/sau, vị trí câu, trọng âm, tốc độ, pitch và người nói. Inventory lớn có nhiều candidate gần đúng context hơn, giảm mức sửa tín hiệu và join cost. Tuy nhiên dung lượng và chi phí tìm kiếm tăng. Hai candidate/unit của Lab chỉ đủ minh họa DP, chưa đủ đạt độ tự nhiên hệ lớn.

## 8. Ít nhất hai khác biệt concatenative và neural TTS?

(1) Concatenative lưu/chọn waveform rồi ghép; neural học ánh xạ text/phoneme sang biểu diễn âm học hoặc waveform. (2) Concatenative phụ thuộc phủ context của inventory, dễ lộ biên; neural cần model và dữ liệu huấn luyện, có thể tạo liên tục nhưng cũng phát âm sai/hallucination/artifact. (3) Chi phí tài nguyên và latency khác theo model/device, không thể kết luận neural luôn nhanh/chậm hơn. Bài đo cùng máy để so sánh cục bộ.

## 9. Vì sao không tải model tùy ý trong giờ Lab để so sánh?

Model khác ngôn ngữ, speaker, phiên bản, license và sample rate gây so sánh thiếu kiểm soát; tải model cũng làm lẫn download với latency inference, có thể hết giờ hoặc thiếu mạng. Cần chuẩn bị backend tương thích offline trước, khóa revision/config và ghi hash. Hai model ở đây đã có sẵn parts và kiểm checksum, không tải lúc inference.

## 10. MOS cao nhưng intelligibility thấp dùng ở đâu?

Cần xác định MOS đang hỏi độ tự nhiên hay chất lượng chung. Nếu giọng dễ chịu nhưng nghe sai nội dung thì không phù hợp thông báo xếp hàng, trợ năng đọc văn bản hoặc thông báo an toàn. Có thể dùng làm hiệu ứng giọng nền hay lời giả không mang thông tin quan trọng, khi người dùng biết đó là nội dung không cần hiểu. Đây chỉ là phạm vi ứng dụng có điều kiện, không biện minh cho TTS đọc sai. Case study Lab phải ưu tiên đúng số khách và quầy.
