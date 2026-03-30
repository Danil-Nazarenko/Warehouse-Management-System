import customtkinter as ctk
import data_manager
import pandas as pd
from datetime import datetime, timedelta
from tkinter import filedialog, messagebox
# Импортируем ваш кастомный поиск
from .components import SmartSearchEntry 

class ActiveInventoryView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        # Состояние пагинации и фильтров
        self.current_filter = "all" 
        self.threshold = 20          
        self.days_lookback = 10 
        self.items_per_page = 50
        self.current_page = 0
        self.filtered_data = [] 
        
        # --- HEADER ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(20, 10))
        
        ctk.CTkLabel(header, text="📊 МОНИТОРИНГ АКТУАЛЬНОГО", 
                     font=("Arial", 22, "bold"), text_color="#3498db").pack(side="left")
        
        # КНОПКА ЭКСПОРТА (вместо обновления)
        self.btn_export = ctk.CTkButton(header, text="📥 ЭКСПОРТ EXCEL", width=140, 
                                         fg_color="#27ae60", hover_color="#219150",
                                         font=("Arial", 12, "bold"), command=self.export_to_excel)
        self.btn_export.pack(side="right")

        # --- ДВУХСТРОЧНЫЙ CONTROL PANEL ---
        self.ctrl_panel = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=8)
        self.ctrl_panel.pack(fill="x", padx=30, pady=5)
        
        # Первая строка: Кнопки фильтров + ПОИСК
        top_row = ctk.CTkFrame(self.ctrl_panel, fg_color="transparent")
        top_row.pack(fill="x", padx=10, pady=(10, 5))
        
        self.btn_all = ctk.CTkButton(top_row, text="ВСЕ АКТИВНЫЕ", width=120, height=32,
                                     fg_color="#3498db", font=("Arial", 11, "bold"),
                                     command=lambda: self.set_filter("all"))
        self.btn_all.pack(side="left", padx=5)
        
        self.btn_low = ctk.CTkButton(top_row, text=f"ДЕФИЦИТ (<{self.threshold})", width=140, height=32,
                                     fg_color="#444444", font=("Arial", 11, "bold"),
                                     command=lambda: self.set_filter("deficit"))
        self.btn_low.pack(side="left", padx=5)

        self.btn_zero = ctk.CTkButton(top_row, text="ОТСУТСТВУЮТ", width=120, height=32,
                                      fg_color="#444444", font=("Arial", 11, "bold"),
                                      command=lambda: self.set_filter("zero"))
        self.btn_zero.pack(side="left", padx=5)

        # ПОИСК
        self.search_entry = SmartSearchEntry(top_row, placeholder_text="Поиск по артикулу...", width=250)
        self.search_entry.pack(side="right", padx=5)
        self.search_entry.bind_search(self.full_reload) 
        
        # Вторая строка: Параметры периода, порога и статистика
        bottom_row = ctk.CTkFrame(self.ctrl_panel, fg_color="transparent")
        bottom_row.pack(fill="x", padx=10, pady=(5, 10))

        ctk.CTkLabel(bottom_row, text="Период:", font=("Arial", 11, "bold"), text_color="#999").pack(side="left", padx=(5, 2))
        self.days_menu = ctk.CTkOptionMenu(bottom_row, width=110, height=28,
                                           values=["Сегодня", "3 дня", "7 дней", "10 дней", "14 дней", "30 дней"],
                                           command=self.change_days_filter)
        self.days_menu.set(f"{self.days_lookback} дней") 
        self.days_menu.pack(side="left", padx=5)

        ctk.CTkLabel(bottom_row, text="Порог:", font=("Arial", 11, "bold"), text_color="#999").pack(side="left", padx=(15, 2))
        self.threshold_entry = ctk.CTkEntry(bottom_row, width=60, height=28, 
                                            placeholder_text=str(self.threshold), justify="center")
        self.threshold_entry.pack(side="left", padx=5)
        self.threshold_entry.bind("<Return>", lambda e: self.update_threshold())

        self.stats_label = ctk.CTkLabel(bottom_row, text="Показано: 0", font=("Arial", 11), text_color="gray")
        self.stats_label.pack(side="right", padx=15)

        # --- TABLE HEADER ---
        self.table_header = ctk.CTkFrame(self, fg_color="#3d3d3d", height=35, corner_radius=4)
        self.table_header.pack(fill="x", padx=30, pady=(10, 0))
        
        ctk.CTkLabel(self.table_header, text="АРТИКУЛ", width=250, anchor="w").pack(side="left", padx=15)
        ctk.CTkLabel(self.table_header, text="БЫЛО", width=100, anchor="w").pack(side="left")
        ctk.CTkLabel(self.table_header, text="ИЗМЕНЕНИЯ", width=120, anchor="w").pack(side="left")
        ctk.CTkLabel(self.table_header, text="ТЕКУЩИЙ", width=150, anchor="w").pack(side="left")

        # --- SCROLLABLE CONTENT ---
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="#2b2b2b", corner_radius=10)
        self.scroll_frame.pack(fill="both", expand=True, padx=30, pady=(5, 5))
        
        # --- PAGINATION FOOTER ---
        self.pagination_frame = ctk.CTkFrame(self, fg_color="transparent", height=40)
        self.pagination_frame.pack(fill="x", padx=30, pady=(5, 15))
        
        self.prev_btn = ctk.CTkButton(self.pagination_frame, text="⬅ Назад", width=80, height=28, 
                                      command=self.prev_page, fg_color="#444")
        self.prev_btn.pack(side="left", padx=5)
        
        self.page_info = ctk.CTkLabel(self.pagination_frame, text="Страница 1 из 1", font=("Arial", 12))
        self.page_info.pack(side="left", padx=20)
        
        self.next_btn = ctk.CTkButton(self.pagination_frame, text="Вперед ➡", width=80, height=28, 
                                      command=self.next_page, fg_color="#444")
        self.next_btn.pack(side="left", padx=5)

        self.full_reload()

    def export_to_excel(self):
        if not self.filtered_data:
            messagebox.showwarning("Экспорт", "Нет данных для экспорта!")
            return
        
        # Подготовка данных для DataFrame
        columns = ["Артикул", "Было (на начало периода)", "Изменение за период", "Текущий остаток"]
        df = pd.DataFrame(self.filtered_data, columns=columns)
        
        # Имя файла по умолчанию с датой и текущим фильтром
        date_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
        default_name = f"Inventory_Report_{self.current_filter}_{date_str}.xlsx"
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            initialfile=default_name,
            filetypes=[("Excel files", "*.xlsx")],
            title="Сохранить отчет"
        )
        
        if file_path:
            try:
                df.to_excel(file_path, index=False)
                messagebox.showinfo("Успех", f"Отчет успешно сохранен:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {e}")

    def change_days_filter(self, choice):
        self.days_lookback = 0 if choice == "Сегодня" else int(choice.split()[0])
        self.full_reload()

    def update_threshold(self):
        val = self.threshold_entry.get()
        if val.isdigit():
            self.threshold = int(val)
            self.btn_low.configure(text=f"ДЕФИЦИТ (<{self.threshold})")
            self.full_reload()

    def set_filter(self, filter_type):
        self.current_filter = filter_type
        self.current_page = 0
        self.btn_all.configure(fg_color="#3498db" if filter_type == "all" else "#444444")
        self.btn_low.configure(fg_color="#d35400" if filter_type == "deficit" else "#444444")
        self.btn_zero.configure(fg_color="#c0392b" if filter_type == "zero" else "#444444")
        self.full_reload()

    def full_reload(self):
        cutoff = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) if self.days_lookback == 0 \
                 else datetime.now() - timedelta(days=self.days_lookback)
        
        active_stats = data_manager.get_active_skus_since(cutoff.strftime("%Y-%m-%d %H:%M:%S"))
        inventory = data_manager.load_json('inventory')
        
        search_query = self.search_entry.get().strip().lower()
        
        self.filtered_data = []
        for sku, stats in sorted(active_stats.items()):
            if search_query and search_query not in sku.lower():
                continue

            current_qty = inventory.get(sku, 0)
            initial_was = stats.get('initial_was', 0)
            
            if self.current_filter == "zero" and current_qty > 0: continue
            if self.current_filter == "deficit" and current_qty > self.threshold: continue
            
            self.filtered_data.append((sku, initial_was, current_qty - initial_was, current_qty))
        
        self.current_page = 0
        self.render_page()

    def render_page(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        total_items = len(self.filtered_data)
        total_pages = max(1, (total_items + self.items_per_page - 1) // self.items_per_page)
        
        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_items = self.filtered_data[start_idx:end_idx]

        if not page_items:
            ctk.CTkLabel(self.scroll_frame, text="Список пуст", font=("Arial", 14), text_color="gray").pack(pady=40)
        else:
            for item in page_items:
                self._draw_row(*item)
        
        self.page_info.configure(text=f"Страница {self.current_page + 1} из {total_pages}")
        self.stats_label.configure(text=f"Всего: {total_items} | Показано: {len(page_items)}")
        
        self.prev_btn.configure(state="normal" if self.current_page > 0 else "disabled")
        self.next_btn.configure(state="normal" if end_idx < total_items else "disabled")
        self.scroll_frame._parent_canvas.yview_moveto(0)

    def next_page(self):
        self.current_page += 1
        self.render_page()

    def prev_page(self):
        self.current_page -= 1
        self.render_page()

    def _draw_row(self, sku, was, change, current):
        row_f = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        row_f.pack(fill="x", pady=1)

        c_color = "#e74c3c" if change < 0 else "#2ecc71"
        c_text = f"{change} шт." if change < 0 else f"+{change} шт."
        if change == 0: 
            c_text = "0 шт."
            c_color = "gray"

        q_color = "#2ecc71"
        if current <= 0: q_color = "#e74c3c"
        elif current <= self.threshold: q_color = "#f39c12"

        ctk.CTkLabel(row_f, text=sku, width=250, anchor="w", font=("Arial", 13)).pack(side="left", padx=10)
        ctk.CTkLabel(row_f, text=f"{was} шт.", width=100, anchor="w", text_color="#bdc3c7").pack(side="left")
        ctk.CTkLabel(row_f, text=c_text, width=120, anchor="w", text_color=c_color, font=("Arial", 13, "bold")).pack(side="left")
        ctk.CTkLabel(row_f, text=f"{current} шт.", width=150, anchor="w", text_color=q_color, font=("Arial", 13, "bold")).pack(side="left")
        
        ctk.CTkFrame(self.scroll_frame, height=1, fg_color="#3d3d3d").pack(fill="x", padx=10)