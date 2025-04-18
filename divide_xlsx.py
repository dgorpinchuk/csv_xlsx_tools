import os
import pandas as pd
from io import BytesIO
from tqdm import tqdm

INPUT_FILE = "input.xlsx"
OUTPUT_DIR = "output"
MAX_SIZE_MB = 20
MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024
CHUNK_SIZE_ROWS = 100000  # Начальное предположение, подбираем дальше

def get_file_size_in_memory(df):
    with BytesIO() as b:
        df.to_excel(b, index=False, engine='openpyxl')
        return b.tell()

def split_and_save(df, base_name, output_dir, max_size_bytes):
    part = 1
    start = 0
    total_rows = len(df)

    print("Начинаем разбиение на части...")
    os.makedirs(output_dir, exist_ok=True)

    with tqdm(total=total_rows, desc="Разбивка и сохранение") as pbar:
        while start < total_rows:
            end = min(start + CHUNK_SIZE_ROWS, total_rows)
            temp_df = df.iloc[start:end]
            size = get_file_size_in_memory(temp_df)

            # Если слишком большой — уменьшаем размер подблока
            while size > max_size_bytes and len(temp_df) > 1:
                end -= len(temp_df) // 2
                temp_df = df.iloc[start:end]
                size = get_file_size_in_memory(temp_df)

            # Сохраняем
            output_path = os.path.join(output_dir, f"part_{part}.xlsx")
            temp_df.to_excel(output_path, index=False, engine='openpyxl')
            file_size_mb = os.path.getsize(output_path) / 1024 / 1024
            print(f"Сохранено: {output_path} ({file_size_mb:.2f} MB, {len(temp_df)} строк)")

            pbar.update(len(temp_df))
            start = end
            part += 1

def main():
    print(f"Загрузка файла {INPUT_FILE}...")
    df = pd.read_excel(INPUT_FILE, engine='openpyxl')
    print(f"Всего строк: {len(df)}")

    split_and_save(df, base_name="output", output_dir=OUTPUT_DIR, max_size_bytes=MAX_SIZE_BYTES)
    print("Готово!")

if __name__ == "__main__":
    main()
