import customtkinter as ctk
import data_manager

class ActiveInventoryView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        # --- ШАПКА ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(20, 10))
        
        ctk.CTkLabel(header, text="📊 МОНИТОРИНГ ЗАКУПОК (ТОП-300)", 
                     font=("Arial", 22, "bold"), text_color="#3498db").pack(side="left")
        
        self.btn_refresh = ctk.CTkButton(header, text="🔄 ОБНОВИТЬ", width=120, 
                                         fg_color="#2ecc71", hover_color="#27ae60",
                                         font=("Arial", 12, "bold"),
                                         command=self.refresh)
        self.btn_refresh.pack(side="right")

        ctk.CTkLabel(self, text="Ниже показаны последние 300 товаров, которые проходили через склад.", 
                     font=("Arial", 12, "italic"), text_color="gray").pack(padx=30, anchor="w")

        # --- ТАБЛИЦА ---
        # Контейнер для заголовков
        self.table_header = ctk.CTkFrame(self, fg_color="#3d3d3d", height=35, corner_radius=4)
        self.table_header.pack(fill="x", padx=30, pady=(10, 0))
        
        ctk.CTkLabel(self.table_header, text="АРТИКУЛ", width=350, anchor="w").pack(side="left", padx=15)
        ctk.CTkLabel(self.table_header, text="ОСТАТОК", width=100, anchor="w").pack(side="left")

        # Область с прокруткой
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="#2b2b2b", corner_radius=10)
        self.scroll_frame.pack(fill="both", expand=True, padx=30, pady=(5, 30))
        
        self.refresh()

    def refresh(self):
        # Очищаем старые строки
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        # Загружаем данные из кэша и актуальный инвентарь
        recent_skus = data_manager.load_json('recent_300')
        inventory = data_manager.load_json('inventory')

        if not recent_skus:
            ctk.CTkLabel(self.scroll_frame, text="История прогонов пуста. Проведите отгрузку или замену.", 
                         font=("Arial", 14)).pack(pady=40)
            return

        # Отрисовка строк
        for sku in recent_skus:
            qty = inventory.get(sku, 0)
            
            # Контейнер строки
            row_f = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
            row_f.pack(fill="x", pady=1)

            # Определяем цвет текста для остатка
            if qty <= 0:
                q_color = "#e74c3c" # Красный - критично
                q_text = "0 шт. (ЗАКАЗАТЬ)"
            elif qty <= 5:
                q_color = "#f1c40f" # Желтый - заканчивается
                q_text = f"{qty} шт."
            else:
                q_color = "#2ecc71" # Зеленый - в норме
                q_text = f"{qty} шт."

            # Артикул
            ctk.CTkLabel(row_f, text=sku, width=350, anchor="w", font=("Arial", 13)).pack(side="left", padx=10)
            
            # Остаток
            ctk.CTkLabel(row_f, text=q_text, width=150, anchor="w", 
                         text_color=q_color, font=("Arial", 13, "bold")).pack(side="left")
            
            # Тонкая разделительная полоска
            ctk.CTkFrame(self.scroll_frame, height=1, fg_color="#3d3d3d").pack(fill="x", padx=10)