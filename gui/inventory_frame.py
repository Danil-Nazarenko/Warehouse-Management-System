import customtkinter as ctk
import data_manager
import warehouse_service 
from tkinter import messagebox
from .components import SmartSearchEntry, OrdoEntry

class InventoryFrame(ctk.CTkFrame):
    def __init__(self, master, search_var, copy_func, **kwargs):
        super().__init__(master, **kwargs)
        self.search_var = search_var
        self.copy_to_clipboard = copy_func
        
        self._inventory_cache = {}
        self._filtered_skus = []
        self._after_id = None 
        self._row_widgets = {}
        
        self.current_page = 0
        self.items_per_page = 50

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(20, 10), padx=20)
        
        left_header = ctk.CTkFrame(header_frame, fg_color="transparent")
        left_header.pack(side="left")

        ctk.CTkLabel(left_header, text="Склад", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")
        
        self.export_btn = ctk.CTkButton(
            left_header, text="📊 Экспорт Excel", width=140, height=32,
            fg_color="#27ae60", hover_color="#219150",
            command=self.handle_export
        )
        self.export_btn.pack(side="left", padx=20)

        self.search_entry = SmartSearchEntry(
            header_frame, placeholder_text="🔍 Поиск артикула...", 
            width=300, textvariable=self.search_var 
        )
        self.search_entry.pack(side="right")
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

        self.bind("<Visibility>", lambda e: self.full_reload_and_refresh())
        self.full_reload_and_refresh()

    def handle_export(self):
        self.export_btn.configure(state="disabled", text="⌛ Экспорт...")
        res = warehouse_service.export_inventory_to_excel()
        self.export_btn.configure(state="normal", text="📊 Экспорт Excel")
        if res["status"] == "success":
            messagebox.showinfo("Готово", res["message"])
        elif res["status"] == "error":
            messagebox.showerror("Ошибка", res["message"])

    def full_reload_and_refresh(self):
        self._inventory_cache = data_manager.load_json('inventory')
        self.refresh()

    def update_sku_ui(self, sku, new_qty):
        """Мгновенное обновление цифры в строке без лишних эффектов."""
        new_qty = int(new_qty)
        self._inventory_cache[sku] = new_qty
        
        if sku in self._row_widgets:
            widgets = self._row_widgets[sku]

            widgets["entry"].delete(0, 'end')
            widgets["entry"].insert(0, str(new_qty))

            card_color = "#3b1e1e" if new_qty < 5 else "#2b2b2b"
            widgets["row"].configure(fg_color=card_color)

    def update_rows(self, updated_data):
        if not updated_data: return
        for sku, qty in updated_data.items():
            self.update_sku_ui(sku, qty)

    def _reset_pagination(self, *args):
        self.current_page = 0
        if self._after_id: self.after_cancel(self._after_id)
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
        if not new_qty_str.strip().replace('-', '').isdigit(): 
            messagebox.showwarning("Ошибка", "Введите число")
            return
        new_qty = int(new_qty_str)
        data_manager.update_inventory_batch({sku: new_qty})
        data_manager.update_recent_300([sku])
        self.update_sku_ui(sku, new_qty)

    def refresh(self):
        if not self.winfo_exists(): return
        query = self.search_var.get().strip().lower()
        if not self._inventory_cache:
            self._inventory_cache = data_manager.load_json('inventory')
        if len(query) >= 3:
            self._filtered_skus = [sku for sku in sorted(self._inventory_cache.keys()) 
                                   if query in sku.lower()]
        else:
            self._filtered_skus = sorted(self._inventory_cache.keys())
        self.render_items()

    def render_items(self):
        for widget in self.scroll_frame.winfo_children(): widget.destroy()
        self._row_widgets = {}
        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        items_to_display = self._filtered_skus[start_idx:end_idx]
        total_pages = (len(self._filtered_skus) - 1) // self.items_per_page + 1 if self._filtered_skus else 1
        self.page_label.configure(text=f"Страница {self.current_page + 1} из {total_pages}")
        self.prev_btn.configure(state="normal" if self.current_page > 0 else "disabled")
        self.next_btn.configure(state="normal" if end_idx < len(self._filtered_skus) else "disabled")

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
            qty_edit = OrdoEntry(edit_frame, width=60, height=28, justify="center")
            qty_edit.insert(0, str(qty))
            qty_edit.pack(side="left", padx=5)
            self._row_widgets[sku] = {"row": row, "entry": qty_edit}
            ctk.CTkButton(edit_frame, text="💾", width=30, height=28, fg_color="#27ae60", 
                          command=lambda s=sku, e=qty_edit: self.manual_update_stock(s, e.get())).pack(side="left")