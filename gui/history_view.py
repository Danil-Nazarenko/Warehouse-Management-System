import customtkinter as ctk
import json
import os
import sys

def get_base_path():
    # Если запущено как EXE
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    
    # Находим папку, где лежит этот файл (gui)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Если мы в папке gui, поднимаемся на уровень выше в корень проекта
    if os.path.basename(current_dir) == 'gui':
        return os.path.dirname(current_dir)
    return current_dir

class HistoryView(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.columnconfigure(1, weight=1)
        self.refresh()

    def refresh(self):
        # Очищаем старые записи перед обновлением
        for widget in self.winfo_children():
            widget.destroy()

        # Теперь путь ведет в корень проекта к history.json
        history_path = os.path.join(get_base_path(), 'history.json')
        
        if not os.path.exists(history_path):
            ctk.CTkLabel(self, text="История пока пуста", font=("Arial", 14, "italic")).grid(row=0, column=0, pady=20)
            return

        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
        except Exception as e:
            ctk.CTkLabel(self, text=f"Ошибка чтения: {e}").grid(row=0, column=0)
            return

        if not history_data:
            ctk.CTkLabel(self, text="В истории нет записей").grid(row=0, column=0, pady=20)
            return

        # Заголовки таблицы
        header_font = ("Arial", 12, "bold")
        ctk.CTkLabel(self, text="Время", font=header_font, text_color="#3b8ed0").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(self, text="Действие", font=header_font, text_color="#3b8ed0").grid(row=0, column=1, padx=10, pady=5, sticky="w")

        # Вывод строк
        for i, entry in enumerate(history_data, start=1):
            # Время
            ctk.CTkLabel(self, text=entry.get("time", ""), font=("Consolas", 11)).grid(row=i, column=0, padx=10, pady=2, sticky="nw")
            
            # Текст действия
            ctk.CTkLabel(self, text=entry.get("action", ""), wraplength=600, justify="left").grid(row=i, column=1, padx=10, pady=2, sticky="nw")
            
            # Разделительная линия
            line = ctk.CTkFrame(self, height=1, fg_color="gray30")
            line.grid(row=i, column=0, columnspan=2, sticky="ew", pady=(5, 0))