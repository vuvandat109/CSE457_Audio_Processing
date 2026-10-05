import pandas as pd
import json


# ==========================================
# Đường dẫn dữ liệu
# ==========================================

file_asr = r"E:\ASR_Project\dataset\asr_results.csv"

file_error = r"E:\ASR_Project\dataset\error_analysis.csv"

file_vietnamese_error = (
    r"E:\ASR_Project\dataset\vietnamese_error_analysis.csv"
)


file_output = (
    r"E:\ASR_Project\dataset\summary_report.json"
)


# ==========================================
# Đọc dữ liệu
# ==========================================

df_asr = pd.read_csv(
    file_asr,
    encoding="utf-8-sig"
)


df_error = pd.read_csv(
    file_error,
    encoding="utf-8-sig"
)


df_vn_error = pd.read_csv(
    file_vietnamese_error,
    encoding="utf-8-sig"
)



# ==========================================
# 1. Thông tin tổng quan
# ==========================================

tong_audio = len(df_asr)



# ==========================================
# 2. WER / CER
# ==========================================

wer_trung_binh = (
    df_asr["wer"]
    .mean()
)


cer_trung_binh = (
    df_asr["cer"]
    .mean()
)



# ==========================================
# 3. S/D/I
# ==========================================

so_thay_the = (
    df_error["substitutions"]
    .sum()
)


so_bo_sot = (
    df_error["deletions"]
    .sum()
)


so_them = (
    df_error["insertions"]
    .sum()
)


so_dung = (
    df_error["hits"]
    .sum()
)



# ==========================================
# 4. Phân tích lỗi tiếng Việt
# ==========================================

thong_ke_loi_tieng_viet = (
    df_vn_error["error_type"]
    .value_counts()
    .to_dict()
)



# ==========================================
# 5. Top lỗi phổ biến
# ==========================================

top_loi = (
    df_vn_error
    [
        [
            "reference_word",
            "hypothesis_word",
            "error_type"
        ]
    ]
    .value_counts()
    .head(10)
)


top_loi_list = []


for item, count in top_loi.items():

    top_loi_list.append({

        "tu_dung": item[0],

        "asr_nhan_dang": item[1],

        "loai_loi": item[2],

        "so_lan": int(count)

    })



# ==========================================
# 6. Tạo báo cáo
# ==========================================

bao_cao = {


    "tong_quan": {

        "so_luong_audio":
            int(tong_audio),

        "WER_trung_binh":
            round(
                float(wer_trung_binh),
                4
            ),

        "CER_trung_binh":
            round(
                float(cer_trung_binh),
                4
            )

    },


    "danh_gia_word": {

        "nhan_dung":
            int(so_dung),

        "thay_the":
            int(so_thay_the),

        "bo_sot":
            int(so_bo_sot),

        "them":
            int(so_them)

    },


    "phan_tich_loi_tieng_viet":
        {
            key:int(value)

            for key,value

            in thong_ke_loi_tieng_viet.items()

        },


    "top_loi_thuong_gap":
        top_loi_list

}



# ==========================================
# Lưu JSON
# ==========================================

with open(
    file_output,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        bao_cao,
        f,
        ensure_ascii=False,
        indent=4
    )


print(
    "===== TAO BAO CAO HOAN TAT ====="
)


print(
    "So audio:",
    tong_audio
)


print(
    "WER:",
    round(
        wer_trung_binh,
        4
    )
)


print(
    "CER:",
    round(
        cer_trung_binh,
        4
    )
)


print(
    "\nThong ke loi:"
)


for key,value in thong_ke_loi_tieng_viet.items():

    print(
        key,
        ":",
        value
    )


print(
    "\nDa tao:"
)

print(
    file_output
)