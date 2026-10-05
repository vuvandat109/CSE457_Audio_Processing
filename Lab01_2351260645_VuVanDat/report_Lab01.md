# CSE457 - XỬ LÝ ÂM THANH VÀ TIẾNG NÓI

# LAB 1: PHÂN TÍCH VÀ XỬ LÝ TÍN HIỆU ÂM THANH SỐ


**Sinh viên:** Vũ Văn Đạt  
**MSSV:** 2351260645  


---

# 1. Giới thiệu

Trong bài thực hành này, tín hiệu âm thanh tiếng nói được phân tích
và xử lý bằng các kỹ thuật xử lý tín hiệu số (Digital Signal Processing - DSP).

Các nội dung thực hiện bao gồm:

- Đọc và phân tích thông tin file âm thanh.
- Phân tích tín hiệu trong miền thời gian.
- Phân tích phổ tần số bằng FFT.
- Phân tích thời gian - tần số bằng STFT.
- Thiết kế bộ lọc FIR.
- Lượng tử hóa tín hiệu âm thanh.
- Đánh giá sai số lượng tử bằng SNR.


---

# 2. Môi trường thực nghiệm


## Công cụ sử dụng

- Python
- Visual Studio Code
- Jupyter Notebook


## Thư viện

|Thư viện|Chức năng|
|NumPy|Tính toán số học|
|Librosa|Xử lý tín hiệu âm thanh|
|SciPy|Thiết kế bộ lọc số|
|Matplotlib|Vẽ biểu đồ|
|SoundFile|Đọc ghi file âm thanh|



# 3. Dữ liệu đầu vào

File âm thanh sử dụng:

audio/input.mp3


Tín hiệu được đọc bằng thư viện Librosa với:

- Giữ nguyên Sampling Rate ban đầu.
- Chuyển về dạng Mono.


# 4. Phân tích thông tin cơ bản của tín hiệu


## 4.1 Phương pháp


Tín hiệu âm thanh được đọc bằng hàm:

```python
librosa.load()

Trong đó:

sr=None: giữ nguyên tần số lấy mẫu gốc.
mono=True: chuyển tín hiệu về một kênh.

Thời lượng tín hiệu được tính:

Duration=Number of Sampling rate

4.2 Kết quả
Thông số	Giá trị
Sampling Rate	48000 Hz
Number of Samples	379008 samples
Duration	7.896 seconds
Channel	Mono

Nhận xét:

Tín hiệu có tần số lấy mẫu 48 kHz, phù hợp với các ứng dụng
xử lý âm thanh số. Tín hiệu được đưa về dạng mono giúp giảm
số lượng dữ liệu và thuận tiện cho quá trình phân tích.

5. Phân tích tín hiệu trong miền thời gian
5.1 Waveform

Dạng sóng biểu diễn sự thay đổi biên độ tín hiệu theo thời gian.

5.2 Các thông số miền thời gian
Peak Amplitude

Peak được tính theo công thức:

Peak=max(|x[n]|) 

Kết quả:

Peak amplitude = 0.87196994

Peak cho biết biên độ lớn nhất của tín hiệu.

RMS

RMS được tính:

RMS=N1​∑x[n]2
​

Kết quả:

RMS = 0.106860965

RMS thể hiện mức năng lượng trung bình của tín hiệu.

Energy

Năng lượng tín hiệu:

Energy=∑x[n]2

Kết quả:

Energy = 4327.993
Tổng hợp kết quả
Thông số	Giá trị
Peak	0.87196994
RMS	0.106860965
Energy	4327.993
6. Phân tích miền tần số bằng FFT
6.1 Phương pháp

FFT được sử dụng để chuyển tín hiệu từ miền thời gian sang miền tần số.

Trong thực nghiệm:

Thông số	Giá trị
Sampling Rate	48000 Hz
FFT points	4096
Window	Hamming

Độ phân giải tần số:

	Giá trị
Sampling Rate	48000 Hz
FFT points	4096
Window	Hamming

Độ phân giải tần số:

Δf=NFFT/Fs
	​
6.2 Kết quả
Frequency resolution = 11.719 Hz

Phổ FFT:

Nhận xét

Kết quả FFT cho thấy năng lượng của tín hiệu tiếng nói tập trung
chủ yếu ở vùng tần số thấp. Đây là đặc điểm phổ biến của tín hiệu
giọng nói con người.

7. Phân tích STFT

STFT được sử dụng để quan sát sự thay đổi thành phần tần số
theo thời gian.

Thông số:

Thông số	Giá trị
FFT size	2048
Window	Hamming
Window length	1200 samples
Hop length	480 samples

Kết quả:

Nhận xét

Spectrogram thể hiện sự phân bố năng lượng của tín hiệu theo
thời gian.

Các vùng sáng biểu diễn các khoảng thời gian tín hiệu có năng lượng
cao hơn, tương ứng với các đoạn phát âm mạnh.

8. Thiết kế bộ lọc FIR
8.1 Low-pass Filter

Thông số:

Thông số	Giá trị
Loại bộ lọc	Low-pass
Số tap	201
Cutoff frequency	2000 Hz

Mục đích:

Giữ lại thành phần tần số thấp.
Giảm thành phần nhiễu tần số cao.
8.2 High-pass Filter

Thông số:

Thông số	Giá trị
Loại bộ lọc	High-pass
Số tap	201
Cutoff frequency	4000 Hz

Mục đích:

Loại bỏ thành phần tần số thấp.
Giữ lại thành phần tần số cao.
Đáp ứng tần số bộ lọc

9. Quantization
9.1 Phương pháp

Lượng tử hóa chuyển đổi tín hiệu liên tục thành các mức biên độ rời rạc.

Số mức lượng tử:

$$ Levels=2^{bits} $$

Các mức khảo sát:

Bit depth	Số mức
4 bit	16
8 bit	256
16 bit	65536
10. Đánh giá SNR
Công thức
SNR=10log10​∑(x−xq​)2∑x2​
Kết quả
Độ phân giải	SNR
4 bit	17.76 dB
8 bit	39.72 dB
16 bit	87.76 dB
Nhận xét

Khi tăng số bit lượng tử hóa:

Số mức biểu diễn tín hiệu tăng.
Sai số lượng tử giảm.
Giá trị SNR tăng.

Kết quả cho thấy lượng tử hóa 16 bit cho chất lượng tín hiệu
tốt nhất do có độ phân giải cao nhất.

11. Kết luận

Qua bài thực hành, tín hiệu âm thanh đã được phân tích và xử lý
bằng các phương pháp DSP cơ bản.

Các kết quả đạt được:

Phân tích được đặc điểm tín hiệu trong miền thời gian.
Xác định thành phần tần số bằng FFT.
Quan sát sự thay đổi phổ bằng STFT.
Thiết kế thành công bộ lọc FIR.
Đánh giá ảnh hưởng của số bit lượng tử hóa bằng SNR.