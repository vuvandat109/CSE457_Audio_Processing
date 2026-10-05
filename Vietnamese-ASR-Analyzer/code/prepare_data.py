import pandas as pd
import os
import shutil
from tqdm import tqdm


# File Common Voice
tsv_file = r"E:\cv-corpus-26.0-2026-06-12\vi\validated.tsv"

# Thư mục chứa audio
audio_folder = r"E:\cv-corpus-26.0-2026-06-12\vi\clips"


# Thư mục xuất ra
output_folder = r"E:\ASR_Project\dataset"

output_audio = os.path.join(output_folder, "audio")

os.makedirs(output_audio, exist_ok=True)


# Đọc TSV
df = pd.read_csv(
    tsv_file,
    sep="\t",
    encoding="utf-8"
)


print("Tổng dữ liệu:", len(df))


# Lọc dữ liệu tốt
df = df[
    (df["up_votes"] >= 2)
    &
    (df["down_votes"] == 0)
]


print("Sau khi lọc:", len(df))


# Lấy 1000 câu
df = df.sample(
    n=1000,
    random_state=42
)


data = []


for _, row in tqdm(df.iterrows(), total=len(df)):

    file_name = row["path"]

    source = os.path.join(
        audio_folder,
        file_name
    )

    destination = os.path.join(
        output_audio,
        file_name
    )


    if os.path.exists(source):

        shutil.copy(
            source,
            destination
        )


        data.append([
            file_name,
            row["sentence"]
        ])



# tạo metadata
metadata = pd.DataFrame(
    data,
    columns=[
        "audio",
        "text"
    ]
)


metadata.to_csv(
    os.path.join(
        output_folder,
        "metadata.csv"
    ),
    index=False,
    encoding="utf-8-sig"
)


print("HOÀN TẤT")
print("Số audio:", len(metadata))