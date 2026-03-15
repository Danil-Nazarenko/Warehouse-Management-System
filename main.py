import customtkinter as ctk
import database 

# Предварительные настройки UI до инициализации основного класса
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class WarehouseApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Минимальная базовая настройка
        database.init_db()
        self.title("Ordo v2.1.0")
        self.geometry("1100x700")
        
        # Переменные поиска
        self.search_var = ctk.StringVar()
        # УДАЛЕНО: self._trace_id = self.search_var.trace_add("write", self.universal_search_handler)
        # Мы больше не вешаем глобальный следящий обработчик, чтобы избежать тормозов.
        
        self.current_view = None
        
        # Кэш для менеджеров
        self._inv_ops = None
        self._shipping = None

        # UI Скелет
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()

        # Основной контейнер
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        # Запускаем первый экран
        self.show_inventory_ui()

    @property
    def inv_ops(self):
        if self._inv_ops is None:
            from gui.inventory_operations import InventoryOperations
            self._inv_ops = InventoryOperations(self)
        return self._inv_ops

    @property
    def shipping(self):
        if self._shipping is None:
            from gui.shipping_frame import ShippingManager
            self._shipping = ShippingManager(self)
        return self._shipping

    def setup_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        
        logo_label = ctk.CTkLabel(self.sidebar_frame, text="📦 OrdO", 
                                  font=ctk.CTkFont(size=28, weight="bold"))
        logo_label.grid(row=0, column=0, padx=20, pady=30)

        # Кнопки меню
        self.create_sidebar_button("📊 Склад", self.show_inventory_ui, 1)
        self.create_sidebar_button("🔥 Актуальное", self.show_active_ui, 2)
        self.create_sidebar_button("📑 Загрузка", lambda: self.shipping.run_morning_orders(), 3)
        self.create_sidebar_button("🚛 Приход", lambda: self.inv_ops.run_supply_ui(), 4)
        self.create_sidebar_button("🔄 Замена", lambda: self.inv_ops.run_swap_ui(), 5)
        self.create_sidebar_button("🛠 Списание", lambda: self.inv_ops.run_waste_ui(), 6)
        self.create_sidebar_button("📦 Каталог", self.show_catalog_ui, 7)
        self.create_sidebar_button("📜 История", self.show_history_ui, 8)

        self.sidebar_frame.grid_rowconfigure(9, weight=1)

        from gui.updater_service import check_for_update
        ctk.CTkButton(self.sidebar_frame, text="Обновление", fg_color="transparent", 
                      border_width=1, command=lambda: check_for_update(self)).grid(row=10, column=0, padx=20, pady=10)
        
        ctk.CTkButton(self.sidebar_frame, text="Выход", fg_color="transparent", 
                      border_width=1, command=self.destroy).grid(row=11, column=0, padx=20, pady=20)

    def create_sidebar_button(self, text, command, row):
        btn = ctk.CTkButton(self.sidebar_frame, text=text, command=command, 
                            height=40, corner_radius=8, fg_color="transparent", anchor="w")
        btn.grid(row=row, column=0, padx=10, pady=5, sticky="ew")
        return btn

    def show_inventory_ui(self):
        from gui.inventory_frame import InventoryFrame
        self.clear_main_frame()
        # Передаем переменную. InventoryFrame сам свяжет её через SmartSearchEntry
        self.current_view = InventoryFrame(self.main_frame, self.search_var, self.copy_to_clipboard)
        self.current_view.pack(fill="both", expand=True)

    def show_active_ui(self):
        from gui.active_view import ActiveInventoryView
        self.clear_main_frame()
        self.current_view = ActiveInventoryView(self.main_frame)
        self.current_view.pack(fill="both", expand=True)

    def show_catalog_ui(self):
        from gui.catalog_frame import CatalogFrame
        self.clear_main_frame()
        self.current_view = CatalogFrame(self.main_frame, self.search_var, self)
        self.current_view.pack(fill="both", expand=True)

    def show_history_ui(self):
        from gui.history_view import HistoryView
        self.clear_main_frame()
        self.current_view = HistoryView(self.main_frame)
        self.current_view.pack(fill="both", expand=True, padx=20, pady=20)

    def clear_main_frame(self):
        """Очищает главный фрейм без лишних манипуляций с переменными поиска."""
        for widget in self.main_frame.winfo_children(): 
            widget.destroy()

    def copy_to_clipboard(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)

if __name__ == "__main__":
    app = WarehouseApp()
    app.mainloop()