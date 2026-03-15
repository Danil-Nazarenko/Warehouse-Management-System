import customtkinter as ctk
from tkinter import filedialog, messagebox
import catalog_service
import data_manager
from .components import SmartSearchEntry

class CatalogFrame(ctk.CTkFrame):
    def __init__(self, master, search_var, parent_app, **kwargs):
        super().__init__(master, **kwargs)
        self.search_var = search_var
        self.parent_app = parent_app  
        self.temp_content = {}        

        # Настройки пагинации для плавности работы
        self.current_page = 0
        self.items_per_page = 50

        # --- ВЕРХНЯЯ ПАНЕЛЬ ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=20, padx=20)
        
        ctk.CTkLabel(header, text="📦 Каталог", font=("Arial", 24, "bold")).pack(side="left")

        # Внедряем умный поиск
        self.search_entry = SmartSearchEntry(
            header, 
            placeholder_text="🔍 Поиск в каталоге (от 3-х симв.)...", 
            width=250, 
            textvariable=self.search_var
        )
        self.search_entry.pack(side="left", padx=20)
        
        # Подписываемся на обновление через компонент
        self.search_entry.bind_search(self._reset_pagination)

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right")
        
        ctk.CTkButton(btn_frame, text="📥 Импорт", fg_color="#27ae60", width=100, 
                      command=self.import_catalog_excel).pack(side="left", padx=5)
        
        ctk.CTkButton(btn_frame, text="+ Добавить", fg_color="#3b8ed0", width=120,
                      command=lambda: self.show_constructor_window()).pack(side="left", padx=5)

        # --- СПИСОК ТОВАРОВ ---
        self.catalog_scroll = ctk.CTkScrollableFrame(self)
        self.catalog_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        # --- БЛОК ПАГИНАЦИИ ---
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
        self.current_page = 0
        self.refresh()

    def _prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh()

    def _next_page(self):
        self.current_page += 1
        self.refresh()

    def refresh(self, *args):
        if not self.winfo_exists():
            return

        search_query = self.search_var.get().strip().lower()
        
        # Защита: не перерисовываем список, если введено всего 1-2 символа
        if 0 < len(search_query) < 3:
            return

        for widget in self.catalog_scroll.winfo_children():
            widget.destroy()
        
        catalog = catalog_service.get_all_items()
        
        # Фильтрация данных
        if len(search_query) >= 3:
            all_matches = [sku for sku in sorted(catalog.keys()) if search_query in sku.lower()]
        else:
            all_matches = sorted(catalog.keys())

        # Расчет страниц
        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        items_to_display = all_matches[start_idx:end_idx]

        # Обновление кнопок навигации
        total_pages = (len(all_matches) - 1) // self.items_per_page + 1 if all_matches else 1
        self.page_label.configure(text=f"Страница {self.current_page + 1} из {total_pages}")
        self.prev_btn.configure(state="normal" if self.current_page > 0 else "disabled")
        self.next_btn.configure(state="normal" if end_idx < len(all_matches) else "disabled")

        if not items_to_display:
            msg = "Ничего не найдено" if len(search_query) >= 3 else "Каталог пуст"
            ctk.CTkLabel(self.catalog_scroll, text=msg, text_color="gray").pack(pady=20)
            return

        for sku in items_to_display:
            items = catalog[sku]
            row = ctk.CTkFrame(self.catalog_scroll, fg_color="#2b2b2b")
            row.pack(fill="x", pady=2, padx=5)
            
            is_bundle = isinstance(items, dict) and len(items) > 0
            icon = "🧺" if is_bundle else "📦"
            label_text = f"{icon} {sku}" + (f" (Состав: {len(items)})" if is_bundle else "")
            
            ctk.CTkLabel(row, text=label_text, anchor="w").pack(side="left", padx=10, pady=5)
            
            # Кнопки управления
            ctk.CTkButton(row, text="✏️", width=30, 
                          command=lambda s=sku: self.show_constructor_window(s)).pack(side="right", padx=5)
            
            ctk.CTkButton(row, text="🗑", width=30, fg_color="#c0392b", 
                          command=lambda s=sku: self.delete_and_refresh(s)).pack(side="right", padx=2)

    def delete_and_refresh(self, sku):
        if messagebox.askyesno("Удаление", f"Удалить {sku} из системы?"):
            catalog_service.delete_item(sku)
            self.refresh()

    def import_catalog_excel(self):
        path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if path:
            res = catalog_service.process_catalog_excel(path)
            if res["status"] == "success":
                messagebox.showinfo("Готово", f"Добавлено артикулов: {res['count']}")
                self.refresh()

    def show_constructor_window(self, edit_sku=None):
        """Окно создания/редактирования набора (Конструктор)"""
        window = ctk.CTkToplevel(self)
        window.title("Конструктор")
        window.geometry("480x400") 
        window.attributes("-topmost", True)
        window.resizable(False, False)

        # Подгружаем состав, если редактируем
        self.temp_content = catalog_service.get_item_content(edit_sku) if edit_sku else {}

        # Поле SKU
        top_f = ctk.CTkFrame(window, fg_color="transparent")
        top_f.pack(fill="x", padx=15, pady=(10, 5))
        ctk.CTkLabel(top_f, text="SKU:", font=("Arial", 12, "bold")).pack(side="left")
        sku_entry = ctk.CTkEntry(top_f, width=320, height=28, placeholder_text="Артикул набора...")
        sku_entry.pack(side="right")
        if edit_sku: 
            sku_entry.insert(0, edit_sku)

        # Панель добавления детали
        add_f = ctk.CTkFrame(window, fg_color="#2b2b2b", height=45)
        add_f.pack(fill="x", padx=15, pady=5)
        
        c_search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(add_f, placeholder_text="Поиск детали...", width=240, height=28, textvariable=c_search_var)
        search_entry.grid(row=0, column=0, padx=(10, 5), pady=8)
        
        qty_entry = ctk.CTkEntry(add_f, width=40, height=28)
        qty_entry.insert(0, "1")
        qty_entry.grid(row=0, column=1, padx=5)

        # Выпадающий список результатов поиска
        search_results_frame = ctk.CTkScrollableFrame(window, height=70, fg_color="#1e1e1e", border_width=1, border_color="#3b8ed0")
        
        # Список уже добавленных частей
        parts_list_frame = ctk.CTkScrollableFrame(window, height=140, label_text="Состав")
        parts_list_frame.pack(fill="both", expand=True, padx=15, pady=5)

        def redraw_parts():
            for w in parts_list_frame.winfo_children(): 
                w.destroy()
            for p, q in self.temp_content.items():
                r = ctk.CTkFrame(parts_list_frame, height=24, fg_color="transparent")
                r.pack(fill="x", pady=0)
                ctk.CTkLabel(r, text=f"• {p} ", font=("Arial", 11)).pack(side="left", padx=2)
                ctk.CTkLabel(r, text=f"x{q}", font=("Arial", 11, "bold"), text_color="#3b8ed0").pack(side="left")
                ctk.CTkButton(r, text="✖", width=16, height=16, fg_color="transparent", 
                              text_color="#e74c3c", hover_color="#3b1e1e",
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
                for w in search_results_frame.winfo_children(): 
                    w.destroy()
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
                c_search_var.set("")
                qty_entry.delete(0, 'end')
                qty_entry.insert(0, "1")
                redraw_parts()
                search_entry.focus()

        def remove_p(p):
            if p in self.temp_content:
                del self.temp_content[p]
                redraw_parts()

        def final_save():
            main_sku = sku_entry.get().strip()
            if not main_sku:
                messagebox.showerror("Ошибка", "Введите артикул!")
                return
            res = catalog_service.save_item(main_sku, self.temp_content)
            if res.get("status") == "success":
                window.destroy()
                self.refresh() # Обновляем список в основном окне
            else:
                messagebox.showerror("Ошибка", res.get('message'))

        ctk.CTkButton(add_f, text="+", width=50, height=28, fg_color="#3b8ed0", 
                      font=("Arial", 16, "bold"), command=add_p).grid(row=0, column=2, padx=(5, 10))
        
        redraw_parts()
        
        ctk.CTkButton(window, text="💾 СОХРАНИТЬ", fg_color="#27ae60", height=35, 
                      font=("Arial", 12, "bold"), command=final_save).pack(pady=(5, 10))