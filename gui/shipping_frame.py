import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import warehouse_service

# ИМПОРТ ЛОГГЕРА
from gui.logger_service import log_action

class ShippingManager:
    def __init__(self, parent_app):
        self.parent = parent_app

    def run_morning_orders(self):
        """Процесс отгрузки заказов с заделом под аналитику"""
        file_path = filedialog.askopenfilename(
            title="Выберите файл заказов",
            filetypes=[("Excel/CSV", "*.xlsx *.csv")]
        )
        
        if not file_path:
            return

        try:
            # 1. Основная логика списания со склада
            warehouse_service.process_morning_orders(file_path)
            
            # ЛОГИРОВАНИЕ В ИСТОРИЮ
            # Берем только название файла без полного пути для чистоты лога
            file_name = os.path.basename(file_path)
            log_action(f"Загрузка заказов: {file_name}")
            
            # 2. МЕСТО ДЛЯ БУДУЩЕЙ АНАЛИТИКИ
            # Здесь мы будем вызывать методы вроде self.update_analytics(file_path)
            
            messagebox.showinfo("Успех", "Заказы успешно обработаны и отгружены!")
            
            # Обновляем интерфейс, если открыт склад
            if self.parent.current_view and hasattr(self.parent.current_view, 'refresh'):
                self.parent.current_view.refresh()
                
        except Exception as e:
            messagebox.showerror("Ошибка отгрузки", f"Произошла ошибка при обработке: {str(e)}")

    def get_shipping_stats(self):
        """Метод-заглушка для будущей выдачи статистики"""
        pass