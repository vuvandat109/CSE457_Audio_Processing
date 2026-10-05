# Vietnamese ASR Analyzer

Hệ thống phân tích và đánh giá mô hình nhận dạng tiếng nói tiếng Việt (Automatic Speech Recognition - ASR).

## 1. Giới thiệu

Dự án xây dựng pipeline đánh giá chất lượng nhận dạng tiếng Việt bằng Whisper.

Hệ thống thực hiện:

- Nhận dạng audio tiếng Việt
- So sánh kết quả ASR với câu chuẩn
- Tính toán WER/CER
- Phân tích lỗi theo đặc điểm tiếng Việt
- Trực quan hóa kết quả bằng Dashboard Web


---

# 2. Kiến trúc hệ thống


Audio Dataset
|
v
Whisper ASR Model
|
v
Text Prediction
|
|
Ground Truth
|
v
WER / CER Evaluation
|
v
Vietnamese Error Analyzer
|
v
FastAPI Backend
|
v
React Dashboard



---

# 3. Công nghệ sử dụng

## AI / Speech

- OpenAI Whisper
- Vietnamese Common Voice Dataset


## Backend

- Python
- FastAPI
- Pandas


## Frontend

- React
- Vite
- Axios
- Recharts


---

# 4. Các chức năng hiện tại

## ASR Evaluation

- Nhận dạng tiếng Việt bằng Whisper
- So sánh với transcript chuẩn


## Metrics

Đánh giá:

- WER (Word Error Rate)
- CER (Character Error Rate)


Kết quả hiện tại:


Audio test: 20 samples

WER:
41.18%

CER:
16.99%



---

# 5. Vietnamese Error Analysis

Hệ thống phân loại lỗi:

| Loại lỗi | Ý nghĩa |
|-|-|
| tone_error | Sai thanh điệu |
| initial_consonant_error | Sai phụ âm đầu |
| final_consonant_error | Sai âm cuối |
| nucleus_error | Sai âm chính |
| medial_error | Sai âm đệm |
| multi_component_error | Sai nhiều thành phần |
| non_vietnamese_token | Ký tự không hợp lệ |


---

# 6. Cấu trúc thư mục


ASR_Project

├── code
│
├── dataset
│
├── web
│ ├── backend
│ │ └── FastAPI
│ │
│ └── frontend
│ └── React Dashboard
│
└── README.md



---

# 7. Chạy Backend


cd web/backend

uvicorn main:app --reload



Backend:


http://127.0.0.1:8000



---

# 8. Chạy Frontend


cd web/frontend

npm install

npm run dev



Frontend:


http://localhost:5173



---

# 9. Roadmap

## Version 1

- Whisper inference
- WER/CER evaluation
- Vietnamese error analyzer


## Version 2

- ASR Dashboard
- Error visualization
- Sentence level analysis


## Version 3

- Upload audio trực tiếp
- Real-time ASR
- Fine-tuning Whisper Vietnamese
- Large-scale evaluation


---

# Author

Vietnamese ASR Analyzer Project