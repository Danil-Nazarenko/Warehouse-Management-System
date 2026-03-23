import customtkinter as ctk
import data_manager
import json

class HistoryView(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.columnconfigure(1, weight=1)
        self.refresh()

    def refresh(self):
        """Полная перезагрузка списка истории. Новые записи уже приходят первыми из SQL."""
        for widget in self.winfo_children():
            widget.destroy()

        try:
            # SQL возвращает данные ORDER BY id DESC (новые сверху)
            history_data = data_manager.load_json('history')
        except Exception as e:
            ctk.CTkLabel(self, text=f"Ошибка БД: {e}").grid(row=0, column=0)
            return

        if not history_data:
            ctk.CTkLabel(self, text="История пуста", font=("Arial", 14, "italic")).grid(row=0, column=0, pady=20)
            return

        header_font = ("Arial", 12, "bold")
        ctk.CTkLabel(self, text="Дата и время", font=header_font).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(self, text="Событие (нажмите для деталей)", font=header_font).grid(row=0, column=1, padx=10, pady=5, sticky="w")

        # Прямой перебор без reversed(), так как SQL уже отсортировал данные
        for i, entry in enumerate(history_data, start=1):
            # Фильтр "пустых кнопок": если нет даты и файла, или детали пустые — пропускаем
            details = entry.get('details', {})
            if not entry.get('date') or not entry.get('filename') or not details:
                continue

            display_text = f"{entry.get('filename', 'Без названия')} — {entry.get('status', 'Неизвестно')}"
            
            ctk.CTkLabel(self, text=entry.get("date", ""), font=("Consolas", 11)).grid(row=i, column=0, padx=10, pady=5, sticky="nw")
            
            btn = ctk.CTkButton(
                self, 
                text=display_text, 
                fg_color="transparent", 
                text_color="#DCE4EE", 
                hover_color="#2B2B2B",
                anchor="w",
                command=lambda e=entry: self.show_details(e)
            )
            btn.grid(row=i, column=1, padx=10, pady=2, sticky="ew")

            line = ctk.CTkFrame(self, height=1, fg_color="gray30")
            line.grid(row=i, column=0, columnspan=2, sticky="ew", pady=(2, 0))

    def show_details(self, entry):
        """Всплывающее окно с таблицей: АРТИКУЛ, БЫЛО, ИЗМ., ИТОГ."""
        raw_details = entry.get('details', {})
        details = json.loads(raw_details) if isinstance(raw_details, str) else raw_details

        detail_window = ctk.CTkToplevel(self)
        detail_window.title(f"Детали: {entry.get('filename')}")
        detail_window.geometry("850x600")
        detail_window.attributes("-topmost", True)

        ctk.CTkLabel(detail_window, text="Движение товара по складу", font=("Arial", 16, "bold")).pack(pady=10)
        
        list_frame = ctk.CTkScrollableFrame(detail_window)
        list_frame.pack(fill="both", expand=True, padx=15, pady=10)

        changes = details.get("Изменения", {})
        old_values = details.get("Было", {})
        
        # Для совместимости со старыми данными
        if not changes and isinstance(details, dict):
            changes = {k: v for k, v in details.items() if k not in ["статистика", "тип"]}

        if changes:
            # Шапка таблицы (используем grid для идеального выравнивания)
            h_frame = ctk.CTkFrame(list_frame, fg_color="gray30")
            h_frame.pack(fill="x", pady=5)
            h_frame.columnconfigure(0, weight=1) # Артикул забирает всё свободное место

            ctk.CTkLabel(h_frame, text="АРТИКУЛ / ОПИСАНИЕ", font=("Arial", 10, "bold"), anchor="w").grid(row=0, column=0, padx=10, sticky="ew")
            ctk.CTkLabel(h_frame, text="БЫЛО", font=("Arial", 10, "bold"), width=70).grid(row=0, column=1, padx=5)
            ctk.CTkLabel(h_frame, text="ИЗМ.", font=("Arial", 10, "bold"), width=70).grid(row=0, column=2, padx=5)
            ctk.CTkLabel(h_frame, text="ИТОГ", font=("Arial", 10, "bold"), width=70).grid(row=0, column=3, padx=10)

            for sku, new_val in changes.items():
                if sku in ["статистика", "тип", "ошибок", "всего_отгружено", "отгружено_штук"]:
                    continue
                
                row = ctk.CTkFrame(list_frame, fg_color="transparent")
                row.pack(fill="x", pady=1)
                row.columnconfigure(0, weight=1)

                # Проверяем, число ли пришло в new_val
                try:
                    # Пытаемся превратить в число для расчетов
                    val_new = float(new_val)
                    old_qty_raw = old_values.get(sku)
                    
                    if old_qty_raw is not None:
                        val_old = float(old_qty_raw)
                        diff = val_new - val_old
                        display_old = str(int(val_old))
                        display_diff = f"{diff:+g}"
                    else:
                        display_old, display_diff, diff = "???", "---", 0
                    
                    diff_color = "#ff6666" if diff < 0 else "#66ff66" if diff > 0 else "#DCE4EE"
                    final_color = "#ff6666" if val_new < 0 else "#DCE4EE"
                    
                    # Рисуем стандартную строку с цифрами (как на вашем образце)
                    ctk.CTkLabel(row, text=str(sku), anchor="w").grid(row=0, column=0, padx=10, sticky="ew")
                    ctk.CTkLabel(row, text=display_old, width=70, text_color="gray").grid(row=0, column=1, padx=5)
                    ctk.CTkLabel(row, text=display_diff, width=70, text_color=diff_color).grid(row=0, column=2, padx=5)
                    ctk.CTkLabel(row, text=str(new_val), width=70, text_color=final_color, font=("Consolas", 12, "bold")).grid(row=0, column=3, padx=10)
                
                except (ValueError, TypeError):
                    # Если в new_val текст, просто выводим его во всю строку (для логов)
                    ctk.CTkLabel(row, text=str(sku), anchor="w", text_color="#A0A0A0").grid(row=0, column=0, padx=10, sticky="ew")
                    # Объединяем ячейки БЫЛО/ИЗМ/ИТОГ для текста
                    ctk.CTkLabel(row, text=str(new_val), anchor="e", text_color="#57bbff", font=("Arial", 11, "italic")).grid(row=0, column=1, columnspan=3, padx=10, sticky="e")

                # Разделительная линия
                ctk.CTkFrame(list_frame, height=1, fg_color="gray25").pack(fill="x", padx=5)
        else:
            ctk.CTkLabel(list_frame, text="Нет данных об изменениях", font=("Arial", 12, "italic")).pack(pady=40)

        ctk.CTkButton(detail_window, text="Закрыть", command=detail_window.destroy).pack(pady=10)