# Скрипт вычленяет почты

import pandas as pd

# Чтение исходного файла
df_original = pd.read_excel('original.xlsx')

# Чтение файла с данными для удаления
df_remove = pd.read_excel('remove.xlsx')

# Сравнение данных по столбцу email и удаление совпадающих строк
df_result = df_original[~df_original['email'].isin(df_remove['email'])]

# Удаление дублирующих строк
df_result = df_result.drop_duplicates()

# Сохранение результата в новый файл
df_result.to_excel('result.xlsx', index=False)

print(f"Завершено")
