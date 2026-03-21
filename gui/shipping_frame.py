import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import warehouse_service
import data_manager 

# ИМПОРТ ЛОГГЕРА
from gui.logger_service import log_action

class ShippingManager:
    def __init__(self, parent_app):
        self.parent = parent_app

    def run_morning_orders(self):
        """Процесс отгрузки заказов с мгновенным обновлением склада"""
        file_path = filedialog.askopenfilename(
            title="Выберите файл заказов",
            filetypes=[("Excel/CSV", "*.xlsx *.csv")]
        )
        
        if not file_path:
            return

        try:
            # 1. Запускаем списание (SQL)
            result = warehouse_service.process_morning_orders(file_path)
            
            if result["status"] == "error":
                messagebox.showerror("Ошибка", result["message"])
                return

            # 2. Логируем результат в БД историю
            file_name = os.path.basename(file_path)
            data_manager.add_history_record(
                file_name, 
                "Успех" if result.get('errors_count') == 0 else "С ошибками",
                {"processed": result.get('processed'), "errors": result.get('errors_count')}
            )
            
            # 3. УМНОЕ ОБНОВЛЕНИЕ ИНТЕРФЕЙСА (Склад)
            # Мы не используем .frames, так как это вызывает ошибку.
            # Мы ищем вкладку склада среди всех дочерних элементов приложения.
            updated_data = result.get("updated_inventory", {})
            
            inventory_view = None
            # Проверяем текущую активную вкладку
            current_view = getattr(self.parent, "current_view", None)
            
            if current_view and hasattr(current_view, 'update_sku_ui'):
                inventory_view = current_view
            else:
                # Если текущая вкладка - не склад, ищем склад среди всех виджетов
                for child in self.parent.winfo_children():
                    if hasattr(child, 'update_sku_ui'):
                        inventory_view = child
                        break
            
            # Если нашли вкладку склада в памяти — обновляем цифры на экране
            if inventory_view:
                for sku, new_qty in updated_data.items():
                    inventory_view.update_sku_ui(sku, new_qty)

            # 4. ВЫВОД РЕЗУЛЬТАТА
            processed = result.get('processed', 0)
            errors_count = result.get('errors_count', 0)
            
            msg = f"Успешно отгружено: {processed} шт."
            if errors_count > 0:
                msg += f"\n\nВнимание! Ошибок: {errors_count}. Проверьте лог дефицита."
                
            messagebox.showinfo("Готово", msg)
                
        except Exception as e:
            # Теперь здесь не будет падения из-за отсутствия .frames
            messagebox.showerror("Ошибка отгрузки", f"Критический сбой: {str(e)}")

    def get_shipping_stats(self):
        pass