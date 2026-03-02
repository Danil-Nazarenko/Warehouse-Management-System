import customtkinter as ctk
import data_manager

class ActiveInventoryView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        # Заголовок
        self.label = ctk.CTkLabel(self, text="📦 МОНИТОРИНГ ХОДОВЫХ ТОВАРОВ", 
                                  font=("Arial", 20, "bold"))
        self.label.pack(pady=20, padx=30, anchor="w")

        # Кнопка обновления
        self.btn_refresh = ctk.CTkButton(self, text="🔄 Обновить список", 
                                         command=self.refresh)
        self.btn_refresh.pack(pady=10, padx=30, anchor="w")

        # Область таблицы
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="#2b2b2b")
        self.scroll.pack(fill="both", expand=True, padx=30, pady=20)
        
        self.refresh()

    def refresh(self):
        # Очистка
        for widget in self.scroll.winfo_children():
            widget.destroy()

        # Берем данные через менеджер
        recent_skus = data_manager.load_json('recent_300')
        inventory = data_manager.load_json('inventory')

        if not recent_skus:
            ctk.CTkLabel(self.scroll, text="Список пуст. Начните работу с товарами.").pack(pady=20)
            return

        # Рисуем строки
        for sku in recent_skus:
            qty = inventory.get(sku, 0)
            
            row = ctk.CTkFrame(self.scroll, fg_color="#333333", height=40)
            row.pack(fill="x", pady=2, padx=5)

            # Цвет остатка
            color = "#e74c3c" if qty <= 0 else "#f1c40f" if qty <= 5 else "#2ecc71"

            ctk.CTkLabel(row, text=sku, width=300, anchor="w").pack(side="left", padx=10)
            ctk.CTkLabel(row, text=f"{qty} шт.", text_color=color, font=("Arial", 13, "bold")).pack(side="left", padx=20)