import wx
import pandas as pd
import requests
from io import StringIO
import os
import re
from datetime import datetime


class ProcessingFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Обработчик файлов", size=(800, 600))

        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Кнопка выбора файла
        btn = wx.Button(panel, label="Выбрать файл")
        btn.Bind(wx.EVT_BUTTON, self.on_select_file)
        sizer.Add(btn, 0, wx.ALL | wx.CENTER, 10)

        # Текстовое поле для лога
        self.log_text = wx.TextCtrl(
            panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL
        )
        font = wx.Font(
            16, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL
        )
        self.log_text.SetFont(font)
        sizer.Add(self.log_text, 1, wx.ALL | wx.EXPAND, 10)

        # Кнопка закрытия
        close_btn = wx.Button(panel, label="Закрыть")
        close_btn.Bind(wx.EVT_BUTTON, self.on_close)
        sizer.Add(close_btn, 0, wx.ALL | wx.CENTER, 10)

        panel.SetSizer(sizer)

        # Сохраняем ссылку на диалог выбора файла
        self.file_dialog = None

    def log(self, message):
        """Добавление сообщения в лог с немедленным обновлением"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"

        # Добавляем сообщение в лог
        self.log_text.AppendText(log_message + "\n")

        # Прокручиваем вниз
        self.log_text.SetInsertionPointEnd()

        # Обновляем интерфейс немедленно
        wx.Yield()

        # Также выводим в консоль
        print(log_message)

    def normalize_text(self, text):
        """Нормализация текста: удаление пробелов, нормализация е/ё и и/й"""
        if pd.isna(text) or text is None:
            return ""

        # Преобразуем в строку и удаляем пробелы в начале и конце
        text = str(text).strip()

        # Нормализуем ё/е и й/и
        text = text.replace("ё", "е").replace("Ё", "Е")
        text = text.replace("й", "и").replace("Й", "И")

        return text

    def names_match(self, name1, name2):
        """Проверка совпадения имен с нормализацией"""
        norm_name1 = self.normalize_text(name1)
        norm_name2 = self.normalize_text(name2)
        return norm_name1.lower() == norm_name2.lower()

    def on_close(self, event):
        """Закрытие приложения"""
        self.Close()

    def on_select_file(self, event):
        """Обработка выбора файла"""
        # Очищаем лог перед новой обработкой
        self.log_text.Clear()

        # Диалог выбора файла
        with wx.FileDialog(
            self,
            "Выберите Excel файл",
            wildcard="Excel files (*.xlsx;*.xls)|*.xlsx;*.xls",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as fileDialog:

            self.file_dialog = fileDialog

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = fileDialog.GetPath()
            self.log(f"Выбран файл: {pathname}")

            try:
                self.process_files(pathname)
                self.log("Обработка завершена!")
                wx.MessageBox(
                    "Обработка завершена!", "Готово", wx.OK | wx.ICON_INFORMATION
                )

                # Закрываем диалог выбора файла
                if self.file_dialog:
                    self.file_dialog = None

            except Exception as e:
                self.log(f"Ошибка: {str(e)}")
                wx.MessageBox(f"Ошибка: {str(e)}", "Ошибка", wx.OK | wx.ICON_ERROR)

    def process_files(self, input_file_path):
        """Основная функция обработки файлов"""
        self.log("Начало обработки...")

        # Чтение исходного Excel файла
        try:
            df_input = pd.read_excel(input_file_path)
            self.log(f"Исходный файл загружен. Количество записей: {len(df_input)}")
        except Exception as e:
            raise Exception(f"Ошибка чтения исходного файла: {str(e)}")

        # Проверка наличия необходимых столбцов
        required_columns = ["Фамилия", "Имя", "Отчество"]
        for col in required_columns:
            if col not in df_input.columns:
                raise Exception(f"Отсутствует столбец: {col}")
        self.log("Проверка структуры исходного файла пройдена")

        # Чтение URL из файла cdn_urls.txt
        try:
            with open("cdn_urls.txt", "r", encoding="utf-8") as f:
                urls = [
                    line.strip()
                    for line in f
                    if line.strip() and not line.strip().startswith("#")
                ]
            self.log(f"Загружено {len(urls)} URL из cdn_urls.txt")
        except Exception as e:
            raise Exception(f"Ошибка чтения файла cdn_urls.txt: {str(e)}")

        # Создание списка для результатов
        results = []
        processed_count = 0

        # Обработка каждого CSV файла
        processed_inputs = set()  # Для отслеживания уже найденных записей

        for i, url in enumerate(urls, 1):
            try:
                self.log(f"Обработка файла {i}/{len(urls)}: {url}")

                # Загрузка CSV файла
                response = requests.get(url, timeout=30)
                response.raise_for_status()

                # Попробуем разные кодировки
                encodings = ["utf-8", "windows-1251", "cp1251"]
                df_csv = None
                csv_content = response.content

                for encoding in encodings:
                    try:
                        csv_text = csv_content.decode(encoding)
                        csv_data = StringIO(csv_text)
                        df_csv = pd.read_csv(csv_data, delimiter=",")
                        self.log(f"  Файл успешно загружен с кодировкой {encoding}")
                        break
                    except:
                        continue

                if df_csv is None:
                    self.log(f"  Ошибка: Не удалось прочитать файл {url}")
                    continue

                # Проверка наличия необходимых столбцов в CSV
                csv_required_columns = ["Фамилия", "Имя", "Отчество"]
                missing_columns = [
                    col for col in csv_required_columns if col not in df_csv.columns
                ]
                if missing_columns:
                    self.log(
                        f"  Предупреждение: Отсутствуют столбцы: {missing_columns}"
                    )
                    continue

                # Сравнение данных
                matches_found = 0
                for idx, input_row in df_input.iterrows():
                    if idx in processed_inputs:
                        continue  # Уже обработано

                    input_key = (
                        self.normalize_text(input_row["Фамилия"]),
                        self.normalize_text(input_row["Имя"]),
                        self.normalize_text(input_row["Отчество"]),
                    )

                    # Поиск совпадений
                    for _, csv_row in df_csv.iterrows():
                        csv_key = (
                            self.normalize_text(csv_row["Фамилия"]),
                            self.normalize_text(csv_row["Имя"]),
                            self.normalize_text(csv_row["Отчество"]),
                        )

                        if input_key == csv_key:
                            # Создание новой строки с данными из CSV + название файла
                            result_row = csv_row.to_dict()
                            result_row["Источник"] = url.split("/")[
                                -1
                            ]  # Имя файла из URL
                            results.append(result_row)
                            processed_inputs.add(idx)
                            matches_found += 1
                            processed_count += 1
                            break

                self.log(f"  Найдено совпадений: {matches_found}")

            except requests.exceptions.Timeout:
                self.log(f"  Ошибка: Таймаут при загрузке файла {url}")
                continue
            except Exception as e:
                self.log(f"  Ошибка обработки файла {url}: {str(e)}")
                continue

        # Добавление не найденных записей
        not_found_count = 0
        for idx, input_row in df_input.iterrows():
            if idx not in processed_inputs:
                # Создаем запись с данными из исходного файла + пометка "Не найден"
                not_found_row = input_row.to_dict()
                not_found_row["Источник"] = "Не найден"
                results.append(not_found_row)
                not_found_count += 1

        self.log(f"Не найдено записей: {not_found_count}")
        self.log(f"Всего обработано: {processed_count}")
        self.log(f"Всего записей в результате: {len(results)}")

        # Создание DataFrame с результатами
        if results:
            df_results = pd.DataFrame(results)

            # Конвертация UID в текстовый формат, если он существует
            if "UID" in df_results.columns:
                df_results["UID"] = df_results["UID"].astype(str)
                self.log("Столбец UID сконвертирован в текстовый формат")
        else:
            # Если результатов нет, создаем пустой DataFrame с базовыми колонками
            df_results = pd.DataFrame(
                columns=["Фамилия", "Имя", "Отчество", "Источник"]
            )

        # Сохранение результата в Excel файл
        output_filename = f"результаты_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        try:
            # Создаем Excel writer с настройками для текстового формата UID
            with pd.ExcelWriter(output_filename, engine="openpyxl") as writer:
                df_results.to_excel(writer, index=False, sheet_name="Результаты")

            self.log(f"Результаты сохранены в файл: {output_filename}")
        except Exception as e:
            raise Exception(f"Ошибка сохранения результата: {str(e)}")

        self.log("Обработка завершена успешно!")


class FileProcessorApp(wx.App):
    def OnInit(self):
        frame = ProcessingFrame()
        frame.Show()
        return True


def main():
    # Создание файла cdn_urls.txt если он не существует (для примера)
    if not os.path.exists("cdn_urls.txt"):
        with open("cdn_urls.txt", "w", encoding="utf-8") as f:
            f.write("# Добавьте сюда URL к CSV файлам\n")
            f.write("# Каждый URL с новой строки\n")
        print("Создан файл cdn_urls.txt. Добавьте в него URL к CSV файлам.")

    app = FileProcessorApp()
    app.MainLoop()


if __name__ == "__main__":
    main()
