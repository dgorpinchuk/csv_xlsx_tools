import wx
import wx.grid
import pandas as pd
import os

PREVIEW_ROWS = 20  # число строк для предпросмотра
CHUNK_SIZE = 5000  # размер чанка для больших файлов

class CSVProcessorFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title="CSV Обработчик", size=(800, 600))
        self.panel = wx.Panel(self)
        self.df = None
        self.csv_path = None

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Кнопка загрузки CSV
        self.load_button = wx.Button(self.panel, label="Выбрать CSV файл")
        self.load_button.Bind(wx.EVT_BUTTON, self.load_csv)
        self.main_sizer.Add(self.load_button, flag=wx.ALL | wx.EXPAND, border=10)

        # Список столбцов для сортировки
        self.columns_label = wx.StaticText(self.panel, label="Выберите столбцы для сортировки:")
        self.columns_checklist = wx.CheckListBox(self.panel, size=(-1, 150), choices=[])
        self.main_sizer.Add(self.columns_label, flag=wx.LEFT | wx.TOP, border=10)
        self.main_sizer.Add(self.columns_checklist, proportion=0, flag=wx.LEFT | wx.RIGHT | wx.EXPAND, border=10)

        # Чекбокс удаления дубликатов
        self.duplicates_check = wx.CheckBox(self.panel, label="Удалить дубликаты")
        self.main_sizer.Add(self.duplicates_check, flag=wx.LEFT | wx.TOP, border=10)

        # Таблица предпросмотра
        self.preview_label = wx.StaticText(self.panel, label=f"Предпросмотр первых {PREVIEW_ROWS} строк:")
        self.main_sizer.Add(self.preview_label, flag=wx.LEFT | wx.TOP, border=10)

        self.grid = wx.grid.Grid(self.panel)
        self.grid.CreateGrid(0, 0)
        self.grid.EnableEditing(False)
        self.main_sizer.Add(self.grid, proportion=1, flag=wx.ALL | wx.EXPAND, border=10)

        # Прогресс-бар
        self.gauge = wx.Gauge(self.panel, range=100, size=(-1, 20))
        self.main_sizer.Add(self.gauge, flag=wx.ALL | wx.EXPAND, border=10)

        # Выбор формата сохранения
        self.format_label = wx.StaticText(self.panel, label="Формат сохранения:")
        self.format_csv = wx.RadioButton(self.panel, label="CSV", style=wx.RB_GROUP)
        self.format_xlsx = wx.RadioButton(self.panel, label="XLSX")
        self.main_sizer.Add(self.format_label, flag=wx.LEFT | wx.TOP, border=10)
        self.main_sizer.Add(self.format_csv, flag=wx.LEFT, border=20)
        self.main_sizer.Add(self.format_xlsx, flag=wx.LEFT, border=20)

        # Кнопка сохранения
        self.save_button = wx.Button(self.panel, label="Сохранить результат")
        self.save_button.Bind(wx.EVT_BUTTON, self.save_file)
        self.main_sizer.Add(self.save_button, flag=wx.ALL | wx.EXPAND, border=10)

        self.panel.SetSizer(self.main_sizer)
        self.Centre()
        self.Show()

    # ---------------------- Загрузка CSV ----------------------
    def load_csv(self, event):
        with wx.FileDialog(self, "Выберите CSV файл", wildcard="CSV files (*.csv)|*.csv",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dialog:

            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return

            self.csv_path = file_dialog.GetPath()
            try:
                # Загружаем весь CSV для возможности сортировки
                self.df = pd.read_csv(self.csv_path)
                self.columns_checklist.Set(self.df.columns.tolist())
                self.update_preview()
            except Exception as e:
                wx.MessageBox(f"Ошибка загрузки файла:\n{e}", "Ошибка", wx.ICON_ERROR, parent=self)

    # ---------------------- Предпросмотр ----------------------
    def update_preview(self):
        if self.df is None:
            return

        preview_df = self.df.head(PREVIEW_ROWS)
        self.grid.ClearGrid()
        if self.grid.GetNumberRows() > 0:
            self.grid.DeleteRows(0, self.grid.GetNumberRows())
        if self.grid.GetNumberCols() > 0:
            self.grid.DeleteCols(0, self.grid.GetNumberCols())

        self.grid.AppendRows(len(preview_df))
        self.grid.AppendCols(len(preview_df.columns))

        for c, col_name in enumerate(preview_df.columns):
            self.grid.SetColLabelValue(c, col_name)
            for r, val in enumerate(preview_df[col_name]):
                self.grid.SetCellValue(r, c, str(val))

        self.grid.AutoSizeColumns()
        self.grid.ForceRefresh()

    # ---------------------- Сохранение CSV/XLSX с прогресс-баром ----------------------
    def save_file(self, event):
        if self.df is None:
            wx.MessageBox("Сначала загрузите CSV файл!", "Ошибка", wx.ICON_WARNING, parent=self)
            return

        selected_indices = self.columns_checklist.GetCheckedItems()
        if not selected_indices:
            wx.MessageBox("Выберите хотя бы один столбец для сортировки!", "Ошибка", wx.ICON_WARNING, parent=self)
            return

        sort_columns = [self.columns_checklist.GetString(i) for i in selected_indices]

        # Диалог выбора пути сохранения
        with wx.FileDialog(self, "Сохранить файл как",
                           wildcard="CSV (*.csv)|*.csv|Excel (*.xlsx)|*.xlsx",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as save_dialog:

            if save_dialog.ShowModal() == wx.ID_CANCEL:
                return

            save_path = save_dialog.GetPath()
            file_ext = os.path.splitext(save_path)[1].lower()

            # Сброс прогресса
            self.gauge.SetValue(0)
            wx.Yield()  # обновление GUI

            if file_ext == ".xlsx" or self.format_xlsx.GetValue():
                # Для XLSX оставляем только выбранные столбцы
                df_result = self.df[sort_columns].sort_values(by=sort_columns)
                if self.duplicates_check.GetValue():
                    df_result = df_result.drop_duplicates()
                df_result.to_excel(save_path, index=False)
                self.gauge.SetValue(100)
            else:
                # CSV с чанками
                total_rows = sum(1 for _ in open(self.csv_path)) - 1  # минус заголовок
                processed_rows = 0
                writer_initialized = False

                for chunk in pd.read_csv(self.csv_path, chunksize=CHUNK_SIZE, usecols=sort_columns):
                    chunk = chunk.sort_values(by=sort_columns)
                    if self.duplicates_check.GetValue():
                        chunk = chunk.drop_duplicates()
                    if not writer_initialized:
                        chunk.to_csv(save_path, mode='w', index=False)
                        writer_initialized = True
                    else:
                        chunk.to_csv(save_path, mode='a', index=False, header=False)
                    processed_rows += len(chunk)
                    progress = min(int(processed_rows / total_rows * 100), 100)
                    self.gauge.SetValue(progress)
                    wx.Yield()  # обновление прогресс-бара

            wx.MessageBox("Файл успешно сохранён!", "Успех", wx.ICON_INFORMATION, parent=self)
            self.Close()


if __name__ == '__main__':
    app = wx.App(False)
    frame = CSVProcessorFrame()
    app.MainLoop()
