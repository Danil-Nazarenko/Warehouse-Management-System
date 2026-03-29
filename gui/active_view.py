import customtkinter as ctk
import data_manager
from datetime import datetime, timedelta

class ActiveInventoryView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        # --- СОСТОЯНИЕ (v2.2.1) ---
        self.current_filter = "all" 
        self.threshold = 20          
        self.days_lookback = 10      # По умолчанию 10 дней
        
        # --- ШАПКА ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(20, 10))
        
        ctk.CTkLabel(header, text="📊 МОНИТОРИНГ АКТУАЛЬНОГО", 
                     font=("Arial", 22, "bold"), text_color="#3498db").pack(side="left")
        
        self.btn_refresh = ctk.CTkButton(header, text="🔄 ОБНОВИТЬ", width=120, 
                                         fg_color="#2ecc71", hover_color="#27ae60",
                                         font=("Arial", 12, "bold"),
                                         command=self.refresh)
        self.btn_refresh.pack(side="right")

        # --- ПАНЕЛЬ УПРАВЛЕНИЯ ---
        self.ctrl_panel = ctk.CTkFrame(self, fg_color="#2b2b2b", height=65, corner_radius=8)
        self.ctrl_panel.pack(fill="x", padx=30, pady=5)
        
        # 1. Фильтры остатков
        self.btn_all = ctk.CTkButton(self.ctrl_panel, text="ВСЕ АКТИВНЫЕ", width=120, height=32,
                                     fg_color="#3498db", font=("Arial", 11, "bold"),
                                     command=lambda: self.set_filter("all"))
        self.btn_all.pack(side="left", padx=(15, 5), pady=15)
        
        self.btn_low = ctk.CTkButton(self.ctrl_panel, text=f"ДЕФИЦИТ (<{self.threshold})", width=120, height=32,
                                     fg_color="#444444", font=("Arial", 11, "bold"),
                                     command=lambda: self.set_filter("deficit"))
        self.btn_low.pack(side="left", padx=5)
        
        self.btn_zero = ctk.CTkButton(self.ctrl_panel, text="ОТСУТСТВУЮТ", width=120, height=32,
                                      fg_color="#444444", font=("Arial", 11, "bold"),
                                      command=lambda: self.set_filter("zero"))
        self.btn_zero.pack(side="left", padx=5)

        # 2. Настройка периода
        ctk.CTkLabel(self.ctrl_panel, text="Период:", font=("Arial", 11, "bold"), text_color="#999").pack(side="left", padx=(20, 5))
        self.days_menu = ctk.CTkOptionMenu(self.ctrl_panel, width=110, height=28,
                                           values=["Сегодня", "3 дня", "7 дней", "10 дней", "14 дней", "30 дней"],
                                           command=self.change_days_filter)
        self.days_menu.set(f"{self.days_lookback} дней") 
        self.days_menu.pack(side="left", padx=5)

        # 3. Статистика и Порог
        self.stats_label = ctk.CTkLabel(self.ctrl_panel, text="Показано: 0", font=("Arial", 11), text_color="gray")
        self.stats_label.pack(side="right", padx=15)

        self.threshold_entry = ctk.CTkEntry(self.ctrl_panel, width=50, height=28, 
                                            placeholder_text=str(self.threshold), justify="center")
        self.threshold_entry.pack(side="right", padx=5)
        self.threshold_entry.bind("<Return>", lambda e: self.update_threshold())
        
        ctk.CTkLabel(self.ctrl_panel, text="Порог:", font=("Arial", 11)).pack(side="right", padx=2)

        # --- ТАБЛИЦА ---
        self.table_header = ctk.CTkFrame(self, fg_color="#3d3d3d", height=35, corner_radius=4)
        self.table_header.pack(fill="x", padx=30, pady=(10, 0))
        
        ctk.CTkLabel(self.table_header, text="АРТИКУЛ", width=350, anchor="w").pack(side="left", padx=15)
        ctk.CTkLabel(self.table_header, text="ТЕКУЩИЙ ОСТАТОК", width=150, anchor="w").pack(side="left")

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="#2b2b2b", corner_radius=10)
        self.scroll_frame.pack(fill="both", expand=True, padx=30, pady=(5, 30))
        
        self.refresh()

    def change_days_filter(self, choice):
        """Обновляет период анализа"""
        if choice == "Сегодня":
            self.days_lookback = 0
        else:
            try:
                self.days_lookback = int(choice.split()[0])
            except (ValueError, IndexError):
                self.days_lookback = 10
        self.refresh()

    def update_threshold(self):
        val = self.threshold_entry.get()
        if val.isdigit():
            self.threshold = int(val)
            self.btn_low.configure(text=f"ДЕФИЦИТ (<{self.threshold})")
            self.refresh()
        else:
            self.threshold_entry.delete(0, 'end')
            self.threshold_entry.insert(0, str(self.threshold))

    def set_filter(self, filter_type):
        self.current_filter = filter_type
        self.btn_all.configure(fg_color="#3498db" if filter_type == "all" else "#444444")
        self.btn_low.configure(fg_color="#d35400" if filter_type == "deficit" else "#444444")
        self.btn_zero.configure(fg_color="#c0392b" if filter_type == "zero" else "#444444")
        self.refresh()

    def get_active_skus_from_history(self):
        """SQL-версия: запрашиваем активные SKU напрямую через базу."""
        try:
            if self.days_lookback == 0:
                cutoff = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                cutoff = datetime.now() - timedelta(days=self.days_lookback)
            
            cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M:%S")
            # Вызов оптимизированного метода из data_manager
            active_list = data_manager.get_active_skus_since(cutoff_str)
            return set(active_list)
        except:
            return set()

    def refresh(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        active_skus = self.get_active_skus_from_history()
        inventory = data_manager.load_json('inventory')

        if not active_skus:
            period_text = "сегодня" if self.days_lookback == 0 else f"последние {self.days_lookback} дн."
            ctk.CTkLabel(self.scroll_frame, text=f"За {period_text} движений не обнаружено.", 
                         font=("Arial", 14), text_color="gray").pack(pady=40)
            self.stats_label.configure(text="Показано: 0")
            return

        count = 0
        for sku in sorted(list(active_skus)):
            qty = inventory.get(sku, 0)
            if self.current_filter == "zero" and qty > 0: continue
            if self.current_filter == "deficit" and qty > self.threshold: continue
            
            count += 1
            self._draw_row(sku, qty)
        
        self.stats_label.configure(text=f"Показано: {count}")
        if count == 0:
            ctk.CTkLabel(self.scroll_frame, text="Нет товаров, подходящих под фильтр.", 
                         font=("Arial", 13), text_color="gray").pack(pady=20)

    def _draw_row(self, sku, qty):
        row_f = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        row_f.pack(fill="x", pady=1)

        if qty <= 0:
            q_color = "#e74c3c"; q_text = f"{qty} шт. (ЗАКАЗАТЬ)"
        elif qty <= self.threshold:
            q_color = "#f39c12"; q_text = f"{qty} шт. (ДЕФИЦИТ)"
        else:
            q_color = "#2ecc71"; q_text = f"{qty} шт."

        ctk.CTkLabel(row_f, text=sku, width=350, anchor="w", font=("Arial", 13)).pack(side="left", padx=10)
        ctk.CTkLabel(row_f, text=q_text, width=200, anchor="w", 
                     text_color=q_color, font=("Arial", 13, "bold")).pack(side="left")
        ctk.CTkFrame(self.scroll_frame, height=1, fg_color="#3d3d3d").pack(fill="x", padx=10)