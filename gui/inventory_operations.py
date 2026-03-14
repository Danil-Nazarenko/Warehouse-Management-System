import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import supply_service
import waste_service
import warehouse_service

# ИМПОРТ НАШЕГО ГОСТ-ПОЛЯ
from .components import OrdoEntry
# ИМПОРТ ЛОГГЕРА
from gui.logger_service import log_action

class InventoryOperations:
    def __init__(self, parent_app):
        self.parent = parent_app
        self.all_skus = []

    # --- УНИВЕРСАЛЬНЫЙ ПОИСК ---
    def _setup_autocomplete(self, combo):
        def on_filter(event):
            if event.keysym in ("Up", "Down", "Return", "Escape", "Tab"):
                return
            val = combo.get().lower()
            matches = [s for s in self.all_skus if val in s.lower()] if val else self.all_skus
            combo.configure(values=matches[:20])

        def on_click(event):
            if not combo._is_open:
                combo._open_dropdown_menu()

        combo._entry.bind("<KeyRelease>", on_filter)
        combo._entry.bind("<Button-1>", on_click)

    # --- ОБЩИЙ ОБРАБОТЧИК ДЛЯ ПРОСТЫХ ОПЕРАЦИЙ ---
    def _execute_operation(self, window, service_func, sku, qty, success_msg="Готово", op_type="Действие"):
        if sku and qty.isdigit():
            res = service_func(sku.strip(), int(qty))
            if res["status"] == "success":
                # ЛОГИРОВАНИЕ УСПЕШНОГО ДЕЙСТВИЯ
                log_action(f"{op_type}: {sku} ({qty} шт.)")
                
                messagebox.showinfo("Успех", res.get("message", success_msg))
                window.destroy()
                self._refresh_ui()
            else:
                messagebox.showerror("Ошибка", res["message"])
        else:
            messagebox.showerror("Ошибка", "Проверьте SKU и количество")

    def run_supply_ui(self):
        window = self._create_popup("Приемка товара", "#2ecc71")
        
        excel_f = ctk.CTkFrame(window, border_width=1, border_color="#2ecc71")
        excel_f.pack(fill="x", padx=30, pady=10)
        ctk.CTkButton(excel_f, text="📂 Выбрать файл Excel", 
                      command=lambda: self._process_supply_excel(window)).pack(pady=10)
        
        ctk.CTkLabel(window, text="── ИЛИ ВРУЧНУЮ ──", text_color="gray").pack(pady=15)
        sku_e = self._create_entry(window, "Артикул (SKU):", "Напр: ABC-123")
        qty_e = self._create_entry(window, "Количество:", "0")
        
        ctk.CTkButton(window, text="✅ ПРИНЯТЬ", fg_color="#27ae60", height=40,
                      command=lambda: self._execute_operation(window, supply_service.add_supply, sku_e.get(), qty_e.get(), op_type="Приход")).pack(pady=20)

    def run_waste_ui(self):
        window = self._create_popup("Списание брака", "#e74c3c")
        sku_e = self._create_entry(window, "Артикул (SKU):", "Введите SKU")
        qty_e = self._create_entry(window, "Количество к списанию:", "0")
        
        ctk.CTkButton(window, text="🗑 СПИСАТЬ", fg_color="#c0392b", height=40,
                      command=lambda: self._execute_operation(window, waste_service.report_defect, sku_e.get(), qty_e.get(), op_type="Брак")).pack(pady=20)

    def run_swap_ui(self):
        self.all_skus = warehouse_service.get_all_skus()
        window = self._create_popup("Мастер замены (Пересорт)", "#3498db")
        window.geometry("450x550")

        ctk.CTkLabel(window, text="1. ТОВАР ИЗ ЗАКАЗА", font=("Arial", 11, "bold")).pack(pady=(20, 0))
        combo_from = ctk.CTkComboBox(window, width=320, values=self.all_skus)
        combo_from.set("")
        combo_from.pack(pady=5)
        self._setup_autocomplete(combo_from)

        ctk.CTkLabel(window, text="2. ТОВАР ПО ФАКТУ", font=("Arial", 11, "bold")).pack(pady=(20, 0))
        combo_to = ctk.CTkComboBox(window, width=320, values=self.all_skus)
        combo_to.set("")
        combo_to.pack(pady=5)
        self._setup_autocomplete(combo_to)

        ctk.CTkLabel(window, text="3. КОЛИЧЕСТВО", font=("Arial", 11, "bold")).pack(pady=(20, 0))
        qty_val = ctk.StringVar(value="1")
        # Здесь тоже используем OrdoEntry для количества
        OrdoEntry(window, textvariable=qty_val, width=80, justify="center").pack(pady=5)

        def confirm_swap():
            s_from, s_to, q = combo_from.get(), combo_to.get(), qty_val.get()
            if s_from and s_to and q.isdigit():
                res = warehouse_service.swap_items(s_from, s_to, int(q))
                if res["status"] == "success":
                    log_action(f"Замена: {s_from} -> {s_to} ({q} шт.)")
                    messagebox.showinfo("Готово", "Склад синхронизирован")
                    window.destroy()
                    self._refresh_ui()
                else: messagebox.showerror("Ошибка", res["message"])
            else: messagebox.showerror("Ошибка", "Заполните данные")

        ctk.CTkButton(window, text="✅ ПОДТВЕРДИТЬ ЗАМЕНУ", fg_color="#3498db", 
                      height=50, width=320, font=("Arial", 12, "bold"), 
                      command=confirm_swap).pack(pady=40)

        combo_from._entry.focus_set()

    def _create_popup(self, title, color):
        win = ctk.CTkToplevel(self.parent)
        win.title(title)
        win.geometry("450x550")
        win.attributes("-topmost", True)
        ctk.CTkLabel(win, text=title.upper(), font=("Arial", 18, "bold"), text_color=color).pack(pady=15)
        return win

    def _create_entry(self, window, label, placeholder=""):
        ctk.CTkLabel(window, text=label).pack()
        # ИСПОЛЬЗОВАНИЕ ГОСТ-ПОЛЯ
        e = OrdoEntry(window, width=250, placeholder_text=placeholder)
        e.pack(pady=5)
        return e

    def _refresh_ui(self):
        if self.parent.current_view and hasattr(self.parent.current_view, 'refresh'):
            self.parent.current_view.refresh()

    def _process_supply_excel(self, win):
        path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if path:
            res = supply_service.process_excel_supply(path)
            if res["status"] == "success":
                f_name = os.path.basename(path)
                log_action(f"Excel-приемка: {f_name} ({res['count']} поз.)")
                messagebox.showinfo("Успех", f"Принято {res['count']} позиций")
                win.destroy()
                self._refresh_ui()
            else: messagebox.showerror("Ошибка", res["message"])