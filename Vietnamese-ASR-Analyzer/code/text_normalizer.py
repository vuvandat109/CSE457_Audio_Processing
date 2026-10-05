import re
import unicodedata

def normalize_vietnamese_text(text):
    # Chuan Unicode
    text = unicodedata.normalize("NFC", text)

    # Viet thuong
    text = text.lower()

    # Bo dau cau, giu lai chu cai tieng Viet va so
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)

    # Xoa khoang trang thua
    text = re.sub(r"\s+", " ", text).strip()

    return text


if __name__ == "__main__":
    ground_truth = "Ở cái nơi rừng thiêng nước độc này."
    prediction = "Um có vungınız hab kh!"

    print("GT:", normalize_vietnamese_text(ground_truth))
    print("PR:", normalize_vietnamese_text(prediction))