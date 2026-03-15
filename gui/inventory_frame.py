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
        
        self.current_page = 0
        self.items_per_page = 50
        
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(20, 10), padx=20)
        
        left_header = ctk.CTkFrame(header_frame, fg_color="transparent")
        left_header.pack(side="left")

        ctk.CTkLabel(left_header, text="Склад", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")
        
        self.export_btn = ctk.CTkButton(
            left_header, 
            text="📊 Экспорт Excel", 
            width=120, 
            height=32,
            fg_color="#27ae60", 
            hover_color="#219150",
            command=self.handle_export
        )
        self.export_btn.pack(side="left", padx=20)

        # "ГОСТовский" компонент: он сам решает, когда вызывать обновление.
        self.search_entry = SmartSearchEntry(
            header_frame, 
            placeholder_text="🔍 Поиск (от 3-х симв.)...", 
            width=300,
            textvariable=self.search_var 
        )
        self.search_entry.pack(side="right")
        
        # ВАЖНО: Мы НЕ используем trace_add здесь, чтобы избежать лишних срабатываний.
        # Вместо этого подписываемся на события компонента.
        self.search_entry.bind_search(self._reset_pagination)

        self.scroll_frame = ctk.CTkScrollableFrame(self, width=800, height=450)
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        self.pagination_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.pagination_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.prev_btn = ctk.CTkButton(self.pagination_frame, text="< Назад", width=80, command=self._prev_page)
        self.prev_btn.pack(side="left", padx=10)
        
        self.page_label = ctk.CTkLabel(self.pagination_frame, text="Страница 1", font=("Arial", 12))
        self.page_label.pack(side="left", expand=True)
        
        self.next_btn = ctk.CTkButton(self.pagination_frame, text="Вперед >", width=80, command=self._next_page)
        self.next_btn.pack(side="right", padx=10)

        self.refresh()

    def _reset_pagination(self, *args):
        # Этот метод вызовется только если введено 0 или 3+ символа
        self.current_page = 0
        self.refresh()

    def _prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh()

    def _next_page(self):
        self.current_page += 1
        self.refresh()

    def handle_export(self):
        res = warehouse_service.export_inventory_to_excel()
        if res["status"] == "success":
            messagebox.showinfo("Готово", res["message"])
        elif res["status"] == "error":
            messagebox.showerror("Ошибка", res["message"])

    def manual_update_stock(self, sku, new_qty_str):
        if not new_qty_str.isdigit(): return
        inventory = data_manager.load_json('inventory')
        inventory[sku] = int(new_qty_str)
        data_manager.save_json('inventory', inventory)
        self.refresh()

    def refresh(self, *args):
        if not self.winfo_exists(): return
        
        # Проверка внутри refresh теперь носит вспомогательный характер, 
        # так как основной фильтр стоит в SmartSearchEntry
        search_query = self.search_var.get().strip().lower()
        
        # Если ввод некорректный (1-2 символа), просто выходим, не стирая текущие виджеты.
        # Это предотвращает "мигание" и лишнюю нагрузку.
        if 0 < len(search_query) < 3:
            return

        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        inventory = data_manager.load_json('inventory')
        
        if len(search_query) >= 3:
            all_matches = [sku for sku in sorted(inventory.keys()) if search_query in sku.lower()]
        else:
            all_matches = sorted(inventory.keys())
        
        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        items_to_display = all_matches[start_idx:end_idx]
        
        total_pages = (len(all_matches) - 1) // self.items_per_page + 1 if all_matches else 1
        self.page_label.configure(text=f"Страница {self.current_page + 1} из {total_pages}")
        
        self.prev_btn.configure(state="normal" if self.current_page > 0 else "disabled")
        self.next_btn.configure(state="normal" if end_idx < len(all_matches) else "disabled")

        if not items_to_display:
            msg = "Ничего не найдено" if len(search_query) >= 3 else "Склад пуст"
            ctk.CTkLabel(self.scroll_frame, text=msg, text_color="gray").pack(pady=20)
            return

        for sku in items_to_display:
            qty = inventory[sku]
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