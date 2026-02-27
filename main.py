import customtkinter as ctk
from gui.inventory_frame import InventoryFrame
from gui.catalog_frame import CatalogFrame

# Новые модули операций
from gui.inventory_operations import InventoryOperations
from gui.shipping_frame import ShippingManager

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class WarehouseApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Ordo v2.0")
        self.geometry("1100x700")
        
        # Переменные
        self.search_var = ctk.StringVar()
        self._trace_id = self.search_var.trace_add("write", self.universal_search_handler)
        self.current_view = None

        # Инициализация менеджеров операций
        self.inv_ops = InventoryOperations(self)
        self.shipping = ShippingManager(self)

        # UI Скелет
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Сейдбар
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        
        # Логотип
        self.logo_container = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.logo_container.grid(row=0, column=0, padx=20, pady=(30, 20))
        ctk.CTkLabel(self.logo_container, text="📦", font=ctk.CTkFont(size=26)).pack(side="left")
        ctk.CTkLabel(self.logo_container, text="Ord", font=ctk.CTkFont(size=32, weight="bold")).pack(side="left")
        ctk.CTkLabel(self.logo_container, text="O", font=ctk.CTkFont(size=34, weight="bold"), text_color="#3b8ed0").pack(side="left")

        # Кнопки меню - теперь все в ряд без дырок
        self.btn_inventory = self.create_sidebar_button("📊 Склад", self.show_inventory_ui, 1)
        self.btn_orders = self.create_sidebar_button("📑 Загрузка заказов", self.shipping.run_morning_orders, 2)
        self.btn_supply = self.create_sidebar_button("🚛 Приход товара", self.inv_ops.run_supply_ui, 3)
        self.btn_swap = self.create_sidebar_button("🔄 Замена (Пересорт)", self.inv_ops.run_swap_ui, 4)
        self.btn_waste = self.create_sidebar_button("🛠 Списание брака", self.inv_ops.run_waste_ui, 5)
        self.btn_catalog = self.create_sidebar_button("📦 Каталог", self.show_catalog_ui, 6)

        # НАСТРОЙКА СЕТКИ: 7-я строка пустая и забирает всё лишнее место
        self.sidebar_frame.grid_rowconfigure(7, weight=1)

        # Кнопка выхода на 8-й строке (будет в самом низу)
        ctk.CTkButton(self.sidebar_frame, text="Выход", fg_color="transparent", border_width=1, command=self.destroy).grid(row=8, column=0, padx=20, pady=20, sticky="s")

        # Контейнер
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        self.show_inventory_ui()

    def create_sidebar_button(self, text, command, row):
        btn = ctk.CTkButton(self.sidebar_frame, text=text, command=command, height=40, corner_radius=8, fg_color="transparent", anchor="w")
        btn.grid(row=row, column=0, padx=10, pady=5, sticky="ew")
        return btn

    def universal_search_handler(self, *args):
        if self.current_view and hasattr(self.current_view, 'refresh'):
            self.current_view.refresh()

    def clear_main_frame(self):
        try: self.search_var.trace_remove("write", self._trace_id)
        except: pass
        for widget in self.main_frame.winfo_children(): 
            widget.destroy()
        self.after(10, self._rebind_search)

    def _rebind_search(self):
        self._trace_id = self.search_var.trace_add("write", self.universal_search_handler)

    def show_inventory_ui(self):
        self.clear_main_frame()
        self.current_view = InventoryFrame(self.main_frame, self.search_var, self.copy_to_clipboard)
        self.current_view.pack(fill="both", expand=True)

    def show_catalog_ui(self):
        self.clear_main_frame()
        self.current_view = CatalogFrame(self.main_frame, self.search_var, self)
        self.current_view.pack(fill="both", expand=True)

    def copy_to_clipboard(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()

    def paste_from_clipboard(self, entry_widget):
        try:
            text = self.clipboard_get()
            entry_widget.delete(0, ctk.END)
            entry_widget.insert(0, text)
        except: pass

if __name__ == "__main__":
    app = WarehouseApp()
    app.mainloop()