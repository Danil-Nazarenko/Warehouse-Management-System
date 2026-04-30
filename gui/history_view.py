import customtkinter as ctk
import data_manager
import json
import math

class HistoryView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.current_page = 1
        self.per_page = 20  # Сколько записей на одной странице

        # Настройка сетки: верх (список) растет, низ (кнопки) зафиксирован
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Область со скроллом для самих записей
        self.scroll_container = ctk.CTkScrollableFrame(self)
        self.scroll_container.grid(row=0, column=0, sticky="nsew", padx=2, pady=(2, 0))
        self.scroll_container.columnconfigure(1, weight=1)

        # 2. Нижняя панель навигации
        self.nav_bar = ctk.CTkFrame(self, height=45, fg_color="transparent")
        self.nav_bar.grid(row=1, column=0, sticky="ew", pady=5)

        self.btn_prev = ctk.CTkButton(self.nav_bar, text="⬅ Назад", width=90, command=self.prev_page)
        self.btn_prev.pack(side="left", padx=20)

        self.page_info = ctk.CTkLabel(self.nav_bar, text="Страница 1", font=("Arial", 12, "bold"))
        self.page_info.pack(side="left", expand=True)

        self.btn_next = ctk.CTkButton(self.nav_bar, text="Вперед ➡", width=90, command=self.next_page)
        self.btn_next.pack(side="right", padx=20)

        self.refresh()

    def refresh(self):
        """Загрузка данных для текущей страницы."""
        # Очищаем только содержимое скролл-контейнера
        for widget in self.scroll_container.winfo_children():
            widget.destroy()

        try:
            # Вызываем твою функцию из data_manager
            history_data, total_count = data_manager.get_history_paginated(self.current_page, self.per_page)
        except Exception as e:
            ctk.CTkLabel(self.scroll_container, text=f"Ошибка БД: {e}").grid(row=0, column=0)
            return

        # Считаем страницы
        total_pages = math.ceil(total_count / self.per_page) if total_count > 0 else 1
        
        # Обновляем UI навигации
        self.page_info.configure(text=f"Страница {self.current_page} из {total_pages}")
        self.btn_prev.configure(state="normal" if self.current_page > 1 else "disabled")
        self.btn_next.configure(state="normal" if self.current_page < total_pages else "disabled")

        if not history_data:
            ctk.CTkLabel(self.scroll_container, text="История пуста", font=("Arial", 14, "italic")).grid(row=0, column=0, pady=20)
            return

        # Шапка таблицы
        header_font = ("Arial", 12, "bold")
        ctk.CTkLabel(self.scroll_container, text="Дата и время", font=header_font).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(self.scroll_container, text="Событие (нажмите для деталей)", font=header_font).grid(row=0, column=1, padx=10, pady=5, sticky="w")

        # Список записей
        for i, entry in enumerate(history_data, start=1):
            details = entry.get('details', {})
            # Небольшой фильтр, как у тебя и было
            if not entry.get('date') or not entry.get('filename') or not details:
                continue

            display_text = f"{entry.get('filename', 'Без названия')} — {entry.get('status', 'Неизвестно')}"
            
            ctk.CTkLabel(self.scroll_container, text=entry.get("date", ""), font=("Consolas", 11)).grid(row=i, column=0, padx=10, pady=5, sticky="nw")
            
            btn = ctk.CTkButton(
                self.scroll_container, 
                text=display_text, 
                fg_color="transparent", 
                text_color="#DCE4EE", 
                hover_color="#2B2B2B",
                anchor="w",
                command=lambda e=entry: self.show_details(e)
            )
            btn.grid(row=i, column=1, padx=10, pady=2, sticky="ew")

            line = ctk.CTkFrame(self.scroll_container, height=1, fg_color="gray30")
            line.grid(row=i, column=0, columnspan=2, sticky="ew", pady=(2, 0))

    def next_page(self):
        self.current_page += 1
        self.refresh()
        self.scroll_container._parent_canvas.yview_moveto(0) # Вверх страницы

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.refresh()
            self.scroll_container._parent_canvas.yview_moveto(0)

    def show_details(self, entry):
        """Окно с деталями записи, поддерживающее внутреннюю пагинацию"""
        raw_details = entry.get('details', {})
        details = json.loads(raw_details) if isinstance(raw_details, str) else raw_details

        # Подготовка данных
        changes = details.get("Изменения", {})
        old_values = details.get("Было", {})
        
        # Если структура простая, превращаем её в словарь изменений
        if not changes and isinstance(details, dict):
            changes = {k: v for k, v in details.items() if k not in ["статистика", "тип"]}

        # Параметры внутренней пагинации
        items_per_page = 50 
        all_skus = list(changes.keys())
        total_items = len(all_skus)
        total_pages = math.ceil(total_items / items_per_page) if total_items > 0 else 1
        
        detail_window = ctk.CTkToplevel(self)
        detail_window.title(f"Детали: {entry.get('filename')}")
        detail_window.geometry("850x700")
        detail_window.attributes("-topmost", True)

        # Состояние текущей страницы окна деталей
        detail_window.current_page = 1

        ctk.CTkLabel(detail_window, text=f"Движение товара: {entry.get('filename')}", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Контейнер для списка
        list_frame = ctk.CTkScrollableFrame(detail_window)
        list_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        # Панель навигации внутри окна деталей
        nav_frame = ctk.CTkFrame(detail_window, fg_color="transparent")
        nav_frame.pack(fill="x", pady=5)

        def render_page():
            # Очистка предыдущих строк
            for widget in list_frame.winfo_children():
                widget.destroy()

            if not all_skus:
                ctk.CTkLabel(list_frame, text="Нет данных об изменениях").pack(pady=20)
                return

            # Шапка (отрисовываем заново на каждой странице для наглядности)
            h_frame = ctk.CTkFrame(list_frame, fg_color="gray30")
            h_frame.pack(fill="x", pady=5)
            h_frame.columnconfigure(0, weight=1)
            ctk.CTkLabel(h_frame, text="АРТИКУЛ / ОПИСАНИЕ", font=("Arial", 10, "bold"), anchor="w").grid(row=0, column=0, padx=10, sticky="ew")
            ctk.CTkLabel(h_frame, text="БЫЛО", font=("Arial", 10, "bold"), width=70).grid(row=0, column=1, padx=5)
            ctk.CTkLabel(h_frame, text="ИЗМ.", font=("Arial", 10, "bold"), width=70).grid(row=0, column=2, padx=5)
            ctk.CTkLabel(h_frame, text="ИТОГ", font=("Arial", 10, "bold"), width=70).grid(row=0, column=3, padx=10)

            # Срез данных для текущей страницы
            start = (detail_window.current_page - 1) * items_per_page
            end = start + items_per_page
            page_items = all_skus[start:end]

            for sku in page_items:
                new_val = changes[sku]
                if sku in ["статистика", "тип", "ошибок", "всего_отгружено", "отгружено_штук"]:
                    continue
                
                row = ctk.CTkFrame(list_frame, fg_color="transparent")
                row.pack(fill="x", pady=1)
                row.columnconfigure(0, weight=1)

                try:
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
                    
                    ctk.CTkLabel(row, text=str(sku), anchor="w").grid(row=0, column=0, padx=10, sticky="ew")
                    ctk.CTkLabel(row, text=display_old, width=70, text_color="gray").grid(row=0, column=1, padx=5)
                    ctk.CTkLabel(row, text=display_diff, width=70, text_color=diff_color).grid(row=0, column=2, padx=5)
                    ctk.CTkLabel(row, text=str(new_val), width=70, text_color=final_color, font=("Consolas", 12, "bold")).grid(row=0, column=3, padx=10)
                except:
                    ctk.CTkLabel(row, text=str(sku), anchor="w", text_color="#A0A0A0").grid(row=0, column=0, padx=10, sticky="ew")
                    ctk.CTkLabel(row, text=str(new_val), anchor="e", text_color="#57bbff", font=("Arial", 11, "italic")).grid(row=0, column=1, columnspan=3, padx=10, sticky="e")

                ctk.CTkFrame(list_frame, height=1, fg_color="gray25").pack(fill="x", padx=5)

            # Обновление текста кнопок
            page_label.configure(text=f"Позиции {start+1}-{min(end, total_items)} из {total_items} (Стр. {detail_window.current_page}/{total_pages})")
            btn_prev_det.configure(state="normal" if detail_window.current_page > 1 else "disabled")
            btn_next_det.configure(state="normal" if detail_window.current_page < total_pages else "disabled")

        def change_page(step):
            detail_window.current_page += step
            render_page()
            list_frame._parent_canvas.yview_moveto(0)

        # Элементы управления в окне деталей
        btn_prev_det = ctk.CTkButton(nav_frame, text="⬅", width=40, command=lambda: change_page(-1))
        btn_prev_det.pack(side="left", padx=10)

        page_label = ctk.CTkLabel(nav_frame, text="")
        page_label.pack(side="left", expand=True)

        btn_next_det = ctk.CTkButton(nav_frame, text="➡", width=40, command=lambda: change_page(1))
        btn_next_det.pack(side="right", padx=10)

        # Первый запуск рендера
        render_page()

        ctk.CTkButton(detail_window, text="Закрыть", command=detail_window.destroy).pack(pady=10)