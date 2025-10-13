import wx
import os
import pandas as pd
import threading

class ConverterFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="XLSX ⇄ CSV Конвертер", size=(400, 200))
        panel = wx.Panel(self)

        vbox = wx.BoxSizer(wx.VERTICAL)

        self.info_text = wx.StaticText(panel, label="Выберите файл для конвертации")
        vbox.Add(self.info_text, 0, wx.ALL | wx.EXPAND, 10)

        self.file_picker = wx.FilePickerCtrl(
            panel, message="Выберите файл", wildcard="Excel (*.xlsx)|*.xlsx|CSV (*.csv)|*.csv"
        )
        vbox.Add(self.file_picker, 0, wx.ALL | wx.EXPAND, 10)

        self.convert_btn = wx.Button(panel, label="Начать")
        vbox.Add(self.convert_btn, 0, wx.ALL | wx.ALIGN_CENTER, 10)

        self.status_text = wx.StaticText(panel, label="")
        vbox.Add(self.status_text, 0, wx.ALL | wx.ALIGN_CENTER, 5)

        panel.SetSizer(vbox)

        self.convert_btn.Bind(wx.EVT_BUTTON, self.on_convert)

        self.progress = None

    def on_convert(self, event):
        file_path = self.file_picker.GetPath()
        if not file_path:
            wx.MessageBox("Пожалуйста, выберите файл.", "Ошибка", wx.OK | wx.ICON_ERROR)
            return

        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".xlsx":
            target_ext = ".csv"
        elif ext == ".csv":
            target_ext = ".xlsx"
        else:
            wx.MessageBox("Поддерживаются только файлы .xlsx и .csv", "Ошибка", wx.OK | wx.ICON_ERROR)
            return

        save_dlg = wx.FileDialog(
            self,
            message="Сохранить как...",
            wildcard=f"*{target_ext}|*{target_ext}",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            defaultFile=os.path.splitext(os.path.basename(file_path))[0] + target_ext
        )
        if save_dlg.ShowModal() != wx.ID_OK:
            return
        output_path = save_dlg.GetPath()

        self.progress = wx.ProgressDialog(
            "Конвертация",
            "Идет обработка файла...",
            maximum=100,
            parent=self,
            style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE | wx.PD_SMOOTH
        )

        threading.Thread(target=self.convert_file, args=(file_path, output_path)).start()

    def convert_file(self, input_path, output_path):
        try:
            ext = os.path.splitext(input_path)[1].lower()
            for i in range(3):
                wx.CallAfter(self.progress.Update, i * 10, "Подготовка...")
                wx.MilliSleep(100)

            if ext == ".xlsx":
                df = pd.read_excel(input_path)
                wx.CallAfter(self.progress.Update, 60, "Сохраняем в CSV...")
                df.to_csv(output_path, index=False)
            else:
                # При чтении CSV, чтобы длинные числа UID не потерялись
                df = pd.read_csv(input_path, dtype=str)
                wx.CallAfter(self.progress.Update, 40, "Обработка UID...")

                # Если есть колонка 'UID', убедимся, что она строковая
                if 'UID' in df.columns:
                    df['UID'] = df['UID'].astype(str)

                wx.CallAfter(self.progress.Update, 60, "Сохраняем в XLSX...")
                df.to_excel(output_path, index=False, engine='openpyxl')

            wx.CallAfter(self.progress.Update, 100, "Готово!")
            wx.CallAfter(self.status_text.SetLabel, f"✅ Конвертация завершена")

        except Exception as e:
            wx.CallAfter(wx.MessageBox, f"Ошибка при конвертации:\n{e}", "Ошибка", wx.OK | wx.ICON_ERROR)
        finally:
            wx.CallAfter(self.progress.Destroy)

class ConverterApp(wx.App):
    def OnInit(self):
        self.frame = ConverterFrame()
        self.frame.Show()
        return True

if __name__ == "__main__":
    app = ConverterApp(False)
    app.MainLoop()
