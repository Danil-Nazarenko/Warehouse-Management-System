import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import supply_service
import waste_service
import warehouse_service
import data_manager  # Для прямой работы с историей без дублей

from .components import OrdoEntry

class InventoryOperations:
    def __init__(self, parent_app):
        self.parent = parent_app
        self.all_skus = []

    def _execute_operation(self, window, service_func, sku, qty, success_msg="Готово", op_type="Действие"):
        sku = sku.strip()
        if sku and qty.isdigit():
            # Запоминаем состояние склада ДО операции
            inv_before = data_manager.load_json('inventory')
            old_qty = inv_before.get(sku, 0)
            
            res = service_func(sku, int(qty))
            if res["status"] == "success":
                # Получаем новое состояние после операции
                updated = res.get("updated_inventory", {})
                new_qty = updated.get(sku, old_qty)
                
                # Формируем правильный словарь для таблицы
                history_details = {
                    "Было": {sku: old_qty},
                    "Изменения": {sku: new_qty}
                }
                
                # Единственная запись в историю — структурированная
                data_manager.add_history_record(
                    filename=f"{op_type}: {sku}",
                    status="Успешно",
                    details=history_details
                )
                
                messagebox.showinfo("Успех", res.get("message", success_msg))
                window.destroy()
                self._refresh_ui(updated)
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
        window = self._create_popup("Мастер замены (Пересорт)", "#3498db")
        sku_from_e = self._create_entry(window, "Заменитель:", "Введите артикул")
        sku_to_e = self._create_entry(window, "Заменяемый:", "Введите артикул")
        qty_e = self._create_entry(window, "КОЛИЧЕСТВО:", "1")

        def confirm_swap():
            s_from = sku_from_e.get().strip()
            s_to = sku_to_e.get().strip()
            q = qty_e.get().strip()
            if s_from and s_to and q.isdigit():
                inv_before = data_manager.load_json('inventory')
                old_f = inv_before.get(s_from, 0)
                old_t = inv_before.get(s_to, 0)

                res = warehouse_service.swap_items(s_from, s_to, int(q))
                if res["status"] == "success":
                    updated = res.get("updated_inventory", {})
                    
                    history_details = {
                        "Было": {s_from: old_f, s_to: old_t},
                        "Изменения": {s_from: updated.get(s_from, 0), s_to: updated.get(s_to, 0)}
                    }
                    
                    # Записываем только структурированную историю
                    data_manager.add_history_record(
                        filename=f"Замена: {s_from} -> {s_to}",
                        status="Готово",
                        details=history_details
                    )

                    messagebox.showinfo("Готово", "Склад синхронизирован")
                    window.destroy()
                    self._refresh_ui(updated)
                else: 
                    messagebox.showerror("Ошибка", res["message"])
            else: 
                messagebox.showerror("Ошибка", "Заполните данные корректно")

        ctk.CTkButton(window, text="✅ ПОДТВЕРДИТЬ ЗАМЕНУ", fg_color="#3498db", 
                      height=50, width=250, font=("Arial", 12, "bold"), 
                      command=confirm_swap).pack(pady=40)

    def _create_popup(self, title, color):
        win = ctk.CTkToplevel(self.parent)
        win.title(title)
        win.geometry("450x550")
        win.attributes("-topmost", True)
        ctk.CTkLabel(win, text=title.upper(), font=("Arial", 18, "bold"), text_color=color).pack(pady=15)
        return win

    def _create_entry(self, window, label, placeholder=""):
        ctk.CTkLabel(window, text=label).pack()
        e = OrdoEntry(window, width=250, placeholder_text=placeholder)
        e.pack(pady=5)
        return e

    def _refresh_ui(self, updated_data=None):
        view = self.parent.current_view
        if not view: return
        if updated_data and hasattr(view, 'update_rows'):
            view.update_rows(updated_data)
        elif not updated_data and hasattr(view, 'full_reload_and_refresh'):
            view.full_reload_and_refresh()

    def _process_supply_excel(self, win):
        path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if path:
            res = supply_service.process_excel_supply(path)
            
            if res["status"] == "success":
                # Формируем детали истории строго по вашей структуре
                history_details = {
                    "Было": res.get("old_inventory", {}),
                    "Изменения": res.get("changes", {}) # Тут лежат новые итоговые остатки
                }
                
                # Записываем в историю
                data_manager.add_history_record(
                    filename=f"Excel: {os.path.basename(path)}",
                    status="Приход",
                    details=history_details
                )
                
                messagebox.showinfo("Успех", f"Принято позиций: {res['count']}")
                win.destroy()
                
                # Передаем обновленные данные в UI, чтобы склад сразу "позеленел"
                self._refresh_ui(res.get("changes"))
            else: 
                messagebox.showerror("Ошибка", res["message"])