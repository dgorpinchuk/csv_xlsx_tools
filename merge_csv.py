import os
import pandas as pd

# Папка с исходными CSV файлами
input_folder = '/Downloads/db'  # замените на путь к вашей папке
output_file = 'merged_output.csv'

# Получаем список всех CSV файлов в папке
csv_files = [f for f in os.listdir(input_folder) if f.endswith('.csv')]

# Список для хранения датафреймов
dfs = []

for file in csv_files:
    file_path = os.path.join(input_folder, file)
    df = pd.read_csv(file_path)
    df['Сезон'] = file  # добавляем столбец с названием файла
    dfs.append(df)

# Объединяем все датафреймы в один
merged_df = pd.concat(dfs, ignore_index=True)

# Сохраняем результат в новый CSV файл
merged_df.to_csv(output_file, index=False)

print(f"Объединённый файл сохранён как: {output_file}")
