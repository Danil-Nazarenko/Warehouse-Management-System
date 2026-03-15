import customtkinter as ctk
import data_manager
import warehouse_service 
from tkinter import messagebox
from .components import SmartSearchEntry

class InventoryFrame(ctk.CTkFrame):
    def __init__(self, master, search_var, copy_func, **kwargs):
        super().__init__(master, **kwargs)
        self.search_var = search_var
        self.copy_to_clipboard = copy_func
        
        # КЭШ: Сюда загружаем данные один раз
        self._inventory_cache = {}
        self._filtered_skus = []
        self._after_id = None  # Для контроля задержки отрисовки
        
        self.current_page = 0
        self.items_per_page = 50
        
        # --- UI СЕКЦИЯ ---
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(20, 10), padx=20)
        
        left_header = ctk.CTkFrame(header_frame, fg_color="transparent")
        left_header.pack(side="left")

        ctk.CTkLabel(left_header, text="Склад", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")
        
        self.export_btn = ctk.CTkButton(
            left_header, text="📊 Экспорт Excel", width=120, height=32,
            fg_color="#27ae60", hover_color="#219150",
            command=self.handle_export
        )
        self.export_btn.pack(side="left", padx=20)

        self.search_entry = SmartSearchEntry(
            header_frame, placeholder_text="🔍 Поиск (от 3-х симв.)...", 
            width=300, textvariable=self.search_var 
        )
        self.search_entry.pack(side="right")
        
        # Привязываем сброс пагинации к поиску
        self.search_entry.bind_search(self._reset_pagination)

        self.scroll_frame = ctk.CTkScrollableFrame(self, width=800, height=450)
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        self.pagination_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.pagination_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.prev_btn = ctk.CTkButton(self.pagination_frame, text="< Назад", width=80, command=self._prev_page)
        self.prev_btn.pack(side="left", padx=10)
        self.page_label = ctk.CTkLabel(self.pagination_frame, text="Страница 1")
        self.page_label.pack(side="left", expand=True)
        self.next_btn = ctk.CTkButton(self.pagination_frame, text="Вперед >", width=80, command=self._next_page)
        self.next_btn.pack(side="right", padx=10)

        # Первая загрузка
        self.full_reload_and_refresh()

    def full_reload_and_refresh(self):
        """Полная принудительная загрузка данных из базы."""
        self._inventory_cache = data_manager.load_json('inventory')
        self.refresh()

    def _reset_pagination(self, *args):
        """Вызывается SmartSearchEntry, когда нужно обновить результаты."""
        self.current_page = 0
        
        # Если была запланирована отрисовка — отменяем
        if self._after_id:
            self.after_cancel(self._after_id)
        
        # Планируем отрисовку через 300 мс после последнего сигнала от поиска
        self._after_id = self.after(300, self.refresh)

    def _prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.render_items()

    def _next_page(self):
        if (self.current_page + 1) * self.items_per_page < len(self._filtered_skus):
            self.current_page += 1
            self.render_items()

    def manual_update_stock(self, sku, new_qty_str):
        if not new_qty_str.isdigit(): return
        # Сохраняем в базу
        inventory = data_manager.load_json('inventory')
        inventory[sku] = int(new_qty_str)
        data_manager.save_json('inventory', inventory)
        
        # Обновляем локальный кэш, чтобы мгновенно увидеть изменения без перезагрузки всей базы
        self._inventory_cache[sku] = int(new_qty_str)
        self.render_items()

    def refresh(self):
        """Фильтрация данных в памяти."""
        if not self.winfo_exists(): return
        
        query = self.search_var.get().strip().lower()
        
        # Если в кэше пусто (например, при старте)
        if not self._inventory_cache:
            self._inventory_cache = data_manager.load_json('inventory')

        # Фильтруем список ключей (SKU)
        if len(query) >= 3:
            self._filtered_skus = [sku for sku in sorted(self._inventory_cache.keys()) 
                                   if query in sku.lower()]
        elif len(query) == 0:
            self._filtered_skus = sorted(self._inventory_cache.keys())
        else:
            # Если 1-2 символа, мы не обновляем список (оставляем старый или пустой)
            return
        
        self.render_items()

    def render_items(self):
        """Тяжелая функция отрисовки виджетов."""
        # Очистка
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        items_to_display = self._filtered_skus[start_idx:end_idx]
        
        total_pages = (len(self._filtered_skus) - 1) // self.items_per_page + 1 if self._filtered_skus else 1
        self.page_label.configure(text=f"Страница {self.current_page + 1} из {total_pages}")
        
        self.prev_btn.configure(state="normal" if self.current_page > 0 else "disabled")
        self.next_btn.configure(state="normal" if end_idx < len(self._filtered_skus) else "disabled")

        if not items_to_display:
            msg = "Ничего не найдено" if len(self.search_var.get()) >= 3 else "Склад пуст"
            ctk.CTkLabel(self.scroll_frame, text=msg, text_color="gray").pack(pady=20)
            return

        # Генерация карточек
        for sku in items_to_display:
            qty = self._inventory_cache.get(sku, 0)
            card_color = "#3b1e1e" if qty < 5 else "#2b2b2b"
            
            row = ctk.CTkFrame(self.scroll_frame, fg_color=card_color, corner_radius=6)
            row.pack(fill="x", pady=2, padx=5)
            
            ctk.CTkButton(row, text="📋", width=30, height=30, fg_color="transparent", 
                          command=lambda s=sku: self.copy_to_clipboard(s)).pack(side="left", padx=5)
            
            ctk.CTkLabel(row, text=sku, font=("Arial", 14), anchor="w").pack(side="left", padx=5, pady=10)
            
            edit_frame = ctk.CTkFrame(row, fg_color="transparent")
            edit_frame.pack(side="right", padx=10)
            
            qty_edit = ctk.CTkEntry(edit_frame, width=60, height=28, justify="center")
            qty_edit.insert(0, str(qty))
            qty_edit.pack(side="left", padx=5)
            
            ctk.CTkButton(edit_frame, text="💾", width=30, height=28, fg_color="#27ae60", 
                          command=lambda s=sku, e=qty_edit: self.manual_update_stock(s, e.get())).pack(side="left")

    def handle_export(self):
        res = warehouse_service.export_inventory_to_excel()
        if res["status"] == "success":
            messagebox.showinfo("Готово", res["message"])