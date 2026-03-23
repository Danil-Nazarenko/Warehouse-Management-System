import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import warehouse_service
import data_manager 

# УБИРАЕМ ИМПОРТ ЛОГГЕРА (он больше не нужен)

class ShippingManager:
    def __init__(self, parent_app):
        self.parent = parent_app

    def run_morning_orders(self):
        """Процесс отгрузки заказов с выводом списка дефицитных товаров"""
        file_path = filedialog.askopenfilename(
            title="Выберите файл заказов",
            filetypes=[("Excel/CSV", "*.xlsx *.csv")]
        )
        
        if not file_path:
            return

        try:
            # 1. Запускаем списание (SQL) 
            # ВНУТРИ этой функции уже происходит ПРАВИЛЬНАЯ запись в историю
            result = warehouse_service.process_morning_orders(file_path)
            
            if result["status"] == "error":
                messagebox.showerror("Критическая ошибка", result["message"])
                return

            # --- ЗДЕСЬ БЫЛ ЛИШНИЙ ВЫЗОВ add_history_record, Я ЕГО УДАЛИЛ ---
            # Теперь не будет создаваться второй "пустой" файл в истории.

            # 2. Обновление интерфейса (Склад)
            updated_data = result.get("updated_inventory", {})
            inventory_view = None
            current_view = getattr(self.parent, "current_view", None)
            
            if current_view and hasattr(current_view, 'update_sku_ui'):
                inventory_view = current_view
            else:
                for child in self.parent.winfo_children():
                    if hasattr(child, 'update_sku_ui'):
                        inventory_view = child
                        break
            
            if inventory_view:
                for sku, new_qty in updated_data.items():
                    inventory_view.update_sku_ui(sku, new_qty)

            # 3. ВЫВОД РЕЗУЛЬТАТА СО СПИСКОМ ТОВАРОВ
            processed = result.get('processed', 0)
            errors_count = result.get('errors_count', 0)
            
            if errors_count > 0:
                deficit_list = result.get('errors', [])
                display_limit = 15
                items_text = "\n".join(deficit_list[:display_limit])
                
                if len(deficit_list) > display_limit:
                    items_text += f"\n... и еще {len(deficit_list) - display_limit} поз."

                msg = (f"Заказы обработаны.\n"
                       f"Всего отгружено: {processed} шт.\n\n"
                       f"СЛЕДУЮЩИЕ ТОВАРЫ УШЛИ В МИНУС:\n"
                       f"{items_text}")
                
                messagebox.showwarning("Внимание: Дефицит", msg)
            else:
                msg = f"Все заказы списаны полностью!\nОбщее количество: {processed} шт."
                messagebox.showinfo("Успех", msg)
                
        except Exception as e:
            messagebox.showerror("Ошибка отгрузки", f"Критический сбой: {str(e)}")

    def get_shipping_stats(self):
        pass