import customtkinter as ctk
from tkinter import filedialog, messagebox
import os

import data_manager
import warehouse_service
import supply_service
import waste_service
import catalog_service

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class WarehouseApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Ordo v2.0")
        self.geometry("1100x700")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.search_var = ctk.StringVar()
        # Сохраняем ID трассировки, чтобы иметь возможность её отключать
        self._trace_id = self.search_var.trace_add("write", self.universal_search_handler)

        # Сейдбар и Логотип
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)
        
        self.logo_container = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.logo_container.grid(row=0, column=0, padx=20, pady=(30, 20))
        ctk.CTkLabel(self.logo_container, text="📦", font=ctk.CTkFont(size=26)).pack(side="left")
        ctk.CTkLabel(self.logo_container, text="Ord", font=ctk.CTkFont(size=32, weight="bold")).pack(side="left")
        ctk.CTkLabel(self.logo_container, text="O", font=ctk.CTkFont(size=34, weight="bold"), text_color="#3b8ed0").pack(side="left")

        self.btn_inventory = self.create_sidebar_button("📊 Склад", self.show_inventory_ui, 1)
        self.btn_orders = self.create_sidebar_button("📑 Загрузка заказов", self.run_morning_orders, 2)
        self.btn_supply = self.create_sidebar_button("🚛 Приход товара", self.run_supply_ui, 3)
        self.btn_waste = self.create_sidebar_button("🛠 Списание брака", self.run_waste_ui, 4)
        self.btn_catalog = self.create_sidebar_button("📦 Каталог", self.run_catalog_ui, 5)

        ctk.CTkButton(self.sidebar_frame, text="Выход", fg_color="transparent", border_width=1, command=self.destroy).grid(row=7, column=0, padx=20, pady=20, sticky="s")

        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        self.scroll_frame = None
        self.catalog_scroll = None
        self.temp_content = {}
        
        self.show_inventory_ui()

    def universal_search_handler(self, *args):
        if self.scroll_frame and self.scroll_frame.winfo_exists():
            self.filter_inventory()
        if self.catalog_scroll and self.catalog_scroll.winfo_exists():
            self.filter_catalog()

    def create_sidebar_button(self, text, command, row):
        btn = ctk.CTkButton(self.sidebar_frame, text=text, command=command, height=40, corner_radius=8, fg_color="transparent", anchor="w")
        btn.grid(row=row, column=0, padx=10, pady=5, sticky="ew")
        return btn

    def clear_main_frame(self):
        """Безопасная очистка главного фрейма с временным отключением поиска"""
        # 1. Отключаем слежку за текстом, чтобы не вызвать ошибку при удалении Entry
        try:
            self.search_var.trace_remove("write", self._trace_id)
        except (AttributeError, ValueError):
            pass

        # 2. Обнуляем ссылки и удаляем виджеты
        self.scroll_frame = None
        self.catalog_scroll = None
        for widget in self.main_frame.winfo_children(): 
            widget.destroy()

        # 3. Возвращаем слежку через короткую паузу, когда Tkinter закончит удаление
        self.after(10, self._rebind_search)

    def _rebind_search(self):
        """Восстановление связи переменной поиска с обработчиком"""
        self._trace_id = self.search_var.trace_add("write", self.universal_search_handler)

    def paste_from_clipboard(self, entry_widget):
        try:
            text = self.clipboard_get()
            entry_widget.delete(0, ctk.END)
            entry_widget.insert(0, text)
        except: pass

    def copy_to_clipboard(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()

    # --- СКЛАД ---
    def manual_update_stock(self, sku, new_qty_str):
        if not new_qty_str.isdigit(): return
        inventory = data_manager.load_json('inventory')
        inventory[sku] = int(new_qty_str)
        data_manager.save_json('inventory', inventory)
        self.filter_inventory()

    def show_inventory_ui(self):
        self.clear_main_frame()
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(20, 10), padx=20)
        ctk.CTkLabel(header_frame, text="Склад", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")
        ctk.CTkEntry(header_frame, placeholder_text="🔍 Поиск...", width=300, textvariable=self.search_var).pack(side="right")
        
        self.scroll_frame = ctk.CTkScrollableFrame(self.main_frame, width=800, height=500)
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.filter_inventory()

    def filter_inventory(self, *args):
        if not self.scroll_frame or not self.scroll_frame.winfo_exists():
            return

        search_query = self.search_var.get().lower()
        for widget in self.scroll_frame.winfo_children(): widget.destroy()
        
        inventory = data_manager.load_json('inventory')
        for sku in sorted(inventory.keys()):
            if search_query in sku.lower():
                qty = inventory[sku]
                card_color = "#3b1e1e" if qty < 5 else "#2b2b2b"
                row = ctk.CTkFrame(self.scroll_frame, fg_color=card_color, corner_radius=6)
                row.pack(fill="x", pady=2)
                ctk.CTkButton(row, text="📋", width=30, height=30, fg_color="transparent", command=lambda s=sku: self.copy_to_clipboard(s)).pack(side="left", padx=5)
                ctk.CTkLabel(row, text=sku, font=("Arial", 14), anchor="w").pack(side="left", padx=5, pady=10)
                edit_frame = ctk.CTkFrame(row, fg_color="transparent")
                edit_frame.pack(side="right", padx=10)
                qty_edit = ctk.CTkEntry(edit_frame, width=60, height=28, justify="center")
                qty_edit.insert(0, str(qty))
                qty_edit.pack(side="left", padx=5)
                ctk.CTkButton(edit_frame, text="💾", width=30, height=28, fg_color="#27ae60", command=lambda s=sku, e=qty_edit: self.manual_update_stock(s, e.get())).pack(side="left")

    # --- КАТАЛОГ ---
    def run_catalog_ui(self):
        self.clear_main_frame()
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.pack(fill="x", pady=20, padx=20)
        ctk.CTkLabel(header, text="📦 Каталог", font=("Arial", 24, "bold")).pack(side="left")

        ctk.CTkEntry(header, placeholder_text="🔍 Поиск в каталоге...", 
                    width=250, textvariable=self.search_var).pack(side="left", padx=20)

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right")
        
        ctk.CTkButton(btn_frame, text="📥 Импорт", fg_color="#27ae60", width=100, 
                      command=self.import_catalog_excel).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="+ Добавить", fg_color="#3b8ed0", width=120,
                      command=lambda: self.show_constructor_window()).pack(side="left", padx=5)

        self.catalog_scroll = ctk.CTkScrollableFrame(self.main_frame)
        self.catalog_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.filter_catalog()

    def filter_catalog(self, *args):
        if not self.catalog_scroll or not self.catalog_scroll.winfo_exists():
            return

        search_query = self.search_var.get().lower()
        for widget in self.catalog_scroll.winfo_children(): widget.destroy()
        
        catalog = catalog_service.get_all_items()
        for sku, items in sorted(catalog.items()):
            if search_query in sku.lower():
                row = ctk.CTkFrame(self.catalog_scroll, fg_color="#2b2b2b")
                row.pack(fill="x", pady=2, padx=5)
                
                is_bundle = isinstance(items, dict) and len(items) > 0
                icon = "🧺" if is_bundle else "📦"
                label_text = f"{icon} {sku}" + (f" (Состав: {len(items)})" if is_bundle else "")
                
                ctk.CTkLabel(row, text=label_text, anchor="w").pack(side="left", padx=10, pady=5)
                
                ctk.CTkButton(row, text="✏️", width=30, command=lambda s=sku: self.show_constructor_window(s)).pack(side="right", padx=5)
                ctk.CTkButton(row, text="🗑", width=30, fg_color="#c0392b", command=lambda s=sku: self.delete_and_refresh(s)).pack(side="right", padx=2)

    # --- ВСПОМОГАТЕЛЬНЫЕ ОКНА И ЛОГИКА ---
    def run_morning_orders(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel/CSV", "*.xlsx *.csv")])
        if file_path:
            try:
                warehouse_service.process_morning_orders(file_path)
                messagebox.showinfo("Готово", "Заказы загружены!")
                self.show_inventory_ui()
            except Exception as e: messagebox.showerror("Ошибка", str(e))

    def run_supply_ui(self):
        window = ctk.CTkToplevel(self)
        window.title("Приемка товара")
        window.geometry("500x580")
        window.attributes("-topmost", True)
        
        ctk.CTkLabel(window, text="ПРИХОД ТОВАРА", font=("Arial", 18, "bold"), text_color="#2ecc71").pack(pady=15)
        
        excel_frame = ctk.CTkFrame(window, border_width=1, border_color="#2ecc71")
        excel_frame.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkLabel(excel_frame, text="Массовая загрузка (Excel)", font=("Arial", 12, "bold")).pack(pady=5)
        
        def ui_process_excel():
            path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
            if path:
                res = supply_service.process_excel_supply(path)
                if res["status"] == "success":
                    messagebox.showinfo("Успех", f"Принято {res['count']} позиций")
                    window.destroy()
                    self.show_inventory_ui()
                else: messagebox.showerror("Ошибка", res["message"])

        ctk.CTkButton(excel_frame, text="📂 Выбрать файл", command=ui_process_excel).pack(pady=10)
        ctk.CTkLabel(window, text="── ИЛИ ВРУЧНУЮ ──", text_color="gray").pack(pady=15)
        ctk.CTkLabel(window, text="Артикул (SKU):").pack()
        
        sku_frame = ctk.CTkFrame(window, fg_color="transparent")
        sku_frame.pack(pady=5)
        entry_sku = ctk.CTkEntry(sku_frame, placeholder_text="Артикул...", width=200)
        entry_sku.pack(side="left", padx=5)
        ctk.CTkButton(sku_frame, text="📋", width=40, command=lambda: self.paste_from_clipboard(entry_sku)).pack(side="left")
        
        ctk.CTkLabel(window, text="Количество:").pack(pady=(10,0))
        entry_qty = ctk.CTkEntry(window, placeholder_text="Количество...", width=250)
        entry_qty.pack(pady=5)

        def confirm():
            sku, qty = entry_sku.get().strip(), entry_qty.get().strip()
            if sku and qty.isdigit():
                res = supply_service.add_supply(sku, int(qty))
                if res["status"] == "success":
                    messagebox.showinfo("Успех", res["message"])
                    window.destroy()
                    self.show_inventory_ui()
            else: messagebox.showerror("Ошибка", "Данные заполнены неверно")
            
        ctk.CTkButton(window, text="✅ ПРИНЯТЬ", command=confirm, fg_color="#27ae60", height=40).pack(pady=20)

    def run_waste_ui(self):
        window = ctk.CTkToplevel(self)
        window.title("Списание брака")
        window.geometry("500x580")
        window.attributes("-topmost", True)
        
        ctk.CTkLabel(window, text="СПИСАНИЕ БРАКА", font=("Arial", 18, "bold"), text_color="#e74c3c").pack(pady=15)
        
        excel_frame = ctk.CTkFrame(window, border_width=1, border_color="#e74c3c")
        excel_frame.pack(fill="x", padx=30, pady=10)
        
        def ui_process_excel_waste():
            path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
            if path:
                res = waste_service.process_excel_waste(path)
                if res["status"] == "success":
                    messagebox.showinfo("Успех", f"Списано {res['count']} позиций")
                    window.destroy()
                    self.show_inventory_ui()

        ctk.CTkButton(excel_frame, text="📂 Выбрать файл", fg_color="#c0392b", command=ui_process_excel_waste).pack(pady=10)
        
        ctk.CTkLabel(window, text="── ИЛИ ВРУЧНУЮ ──", text_color="gray").pack(pady=15)
        ctk.CTkLabel(window, text="Артикул (SKU):").pack()
        
        sku_frame = ctk.CTkFrame(window, fg_color="transparent")
        sku_frame.pack(pady=5)
        entry_sku = ctk.CTkEntry(sku_frame, placeholder_text="Артикул...", width=200)
        entry_sku.pack(side="left", padx=5)
        ctk.CTkButton(sku_frame, text="📋", width=40, command=lambda: self.paste_from_clipboard(entry_sku)).pack(side="left")
        
        ctk.CTkLabel(window, text="Количество к списанию:").pack(pady=(10,0))
        entry_qty = ctk.CTkEntry(window, placeholder_text="Число...", width=250)
        entry_qty.pack(pady=5)

        def confirm_waste():
            sku, qty = entry_sku.get().strip(), entry_qty.get().strip()
            if not sku or not qty.isdigit(): return
            res = waste_service.report_defect(sku, int(qty))
            if res["status"] == "success":
                messagebox.showinfo("Успех", res["message"])
                window.destroy()
                self.show_inventory_ui()
                
        ctk.CTkButton(window, text="🗑 СПИСАТЬ", command=confirm_waste, fg_color="#c0392b", height=40).pack(pady=20)

    def delete_and_refresh(self, sku):
        if messagebox.askyesno("Удаление", f"Удалить {sku} из системы?"):
            catalog_service.delete_item(sku)
            self.run_catalog_ui()

    def import_catalog_excel(self):
        path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if path:
            res = catalog_service.process_catalog_excel(path)
            if res["status"] == "success":
                messagebox.showinfo("Готово", f"Добавлено артикулов: {res['count']}")
                self.run_catalog_ui()

    def show_constructor_window(self, edit_sku=None):
        window = ctk.CTkToplevel(self)
        window.title("Конструктор")
        window.geometry("480x400") 
        window.attributes("-topmost", True)
        window.resizable(False, False)

        self.temp_content = catalog_service.get_item_content(edit_sku) if edit_sku else {}

        top_f = ctk.CTkFrame(window, fg_color="transparent")
        top_f.pack(fill="x", padx=15, pady=(10, 5))
        ctk.CTkLabel(top_f, text="SKU:", font=("Arial", 12, "bold")).pack(side="left")
        sku_entry = ctk.CTkEntry(top_f, width=320, height=28, placeholder_text="Артикул набора...")
        sku_entry.pack(side="right")
        if edit_sku: sku_entry.insert(0, edit_sku)

        add_f = ctk.CTkFrame(window, fg_color="#2b2b2b", height=45)
        add_f.pack(fill="x", padx=15, pady=5)
        
        c_search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(add_f, placeholder_text="Поиск детали...", width=240, height=28, textvariable=c_search_var)
        search_entry.grid(row=0, column=0, padx=(10, 5), pady=8)
        
        qty_entry = ctk.CTkEntry(add_f, width=40, height=28)
        qty_entry.insert(0, "1")
        qty_entry.grid(row=0, column=1, padx=5)
        
        search_results_frame = ctk.CTkScrollableFrame(window, height=70, fg_color="#1e1e1e", border_width=1, border_color="#3b8ed0")
        search_results_frame.pack_forget()

        parts_list_frame = ctk.CTkScrollableFrame(window, height=140, label_text="Состав")
        parts_list_frame.pack(fill="both", expand=True, padx=15, pady=5)

        def redraw_parts():
            for w in parts_list_frame.winfo_children(): w.destroy()
            for p, q in self.temp_content.items():
                r = ctk.CTkFrame(parts_list_frame, height=24, fg_color="transparent")
                r.pack(fill="x", pady=0)
                ctk.CTkLabel(r, text=f"• {p} ", font=("Arial", 11)).pack(side="left", padx=2)
                ctk.CTkLabel(r, text=f"x{q}", font=("Arial", 11, "bold"), text_color="#3b8ed0").pack(side="left")
                ctk.CTkButton(r, text="✖", width=16, height=16, fg_color="transparent", text_color="#e74c3c", hover_color="#3b1e1e",
                              command=lambda x=p: remove_p(x)).pack(side="right", padx=5)

        def select_item(sku):
            c_search_var.set(sku)
            search_results_frame.pack_forget()
            qty_entry.focus()

        def update_c_search(*args):
            text = c_search_var.get().lower()
            if len(text) < 1:
                search_results_frame.pack_forget()
                return
            inventory = data_manager.load_json('inventory')
            matches = [sku for sku in inventory.keys() if text in sku.lower()]
            if matches:
                search_results_frame.pack(after=add_f, fill="x", padx=25)
                for w in search_results_frame.winfo_children(): w.destroy()
                for sku in matches[:5]:
                    btn = ctk.CTkButton(search_results_frame, text=sku, fg_color="transparent", height=18, anchor="w", font=("Arial", 11),
                                        command=lambda s=sku: select_item(s))
                    btn.pack(fill="x")
            else:
                search_results_frame.pack_forget()

        c_search_var.trace_add("write", update_c_search)

        def add_p():
            sku = c_search_var.get().strip()
            q = qty_entry.get()
            if sku and q.isdigit():
                self.temp_content[sku] = self.temp_content.get(sku, 0) + int(q)
                c_search_var.set(""); qty_entry.delete(0, 'end'); qty_entry.insert(0, "1")
                redraw_parts(); search_entry.focus()

        def remove_p(p):
            if p in self.temp_content:
                del self.temp_content[p]; redraw_parts()

        def final_save():
            main_sku = sku_entry.get().strip()
            if not main_sku:
                messagebox.showerror("Ошибка", "Введите артикул!"); return
            res = catalog_service.save_item(main_sku, self.temp_content)
            if res.get("status") == "success":
                window.destroy(); self.run_catalog_ui()
            else: messagebox.showerror("Ошибка", res.get('message'))

        ctk.CTkButton(add_f, text="+", width=50, height=28, fg_color="#3b8ed0", font=("Arial", 16, "bold"), command=add_p).grid(row=0, column=2, padx=(5, 10))
        redraw_parts()
        ctk.CTkButton(window, text="💾 СОХРАНИТЬ", fg_color="#27ae60", height=35, font=("Arial", 12, "bold"), command=final_save).pack(pady=(5, 10))

if __name__ == "__main__":
    app = WarehouseApp()
    app.mainloop()