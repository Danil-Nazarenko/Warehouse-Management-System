import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import warehouse_service
import data_manager

# Импортируем оба компонента
from .components import OrdoEntry, SmartSearchEntry

class ShippingManager:
    def __init__(self, parent_app):
        self.parent = parent_app
        self._selected_file_path = None

    def _create_popup(self, title, color):
        win = ctk.CTkToplevel(self.parent)
        win.title(title)
        win.geometry("450x650") 
        win.attributes("-topmost", True)
        win.resizable(False, False)
        
        ctk.CTkLabel(
            win, text=title.upper(), 
            font=("Arial", 18, "bold"), 
            text_color=color
        ).pack(pady=20)
        return win

    def run_morning_orders(self):
        window = self._create_popup("Загрузка / Отгрузка", "#3498db")
        
        # --- СЕКЦИЯ EXCEL (Верхняя) ---
        excel_frame = ctk.CTkFrame(window, border_width=1, border_color="#3498db")
        excel_frame.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkButton(
            excel_frame, text="📂 ВЫБРАТЬ ФАЙЛ EXCEL / CSV", 
            height=45, fg_color="#2980b9", hover_color="#3498db",
            command=lambda: self._process_excel_immediately(window)
        ).pack(pady=15, padx=20)

        ctk.CTkLabel(window, text="── ИЛИ ВРУЧНУЮ ──", text_color="gray", font=("Arial", 10)).pack(pady=10)

        # --- 1. ПОЛЕ ВВОДА SKU ---
        ctk.CTkLabel(window, text="АРТИКУЛ (SKU):", font=("Arial", 11, "bold")).pack()
        sku_entry = SmartSearchEntry(window, placeholder_text="Поиск...", width=300, height=36)
        sku_entry.pack(pady=5)

        # --- 2. ВЫДЕЛЕННОЕ ПОЛЕ ДЛЯ СПИСКА (ФИКСИРОВАННОЕ) ---
        # Это и есть то "отдельное поле", про которое ты говорил. 
        # Оно всегда на экране, поэтому ничего не прыгает.
        results_container = ctk.CTkFrame(window, height=150, width=320, fg_color="#1e1e1e", border_width=1, border_color="#333333")
        results_container.pack(pady=5)
        results_container.pack_propagate(False) # Запрещаем менять размер, чтобы окно не моргало

        suggest_scroll = ctk.CTkScrollableFrame(results_container, fg_color="transparent")
        suggest_scroll.pack(fill="both", expand=True)

        def on_search_update():
            query = sku_entry.internal_var.get().strip().lower()
            # Очищаем только содержимое скролла
            for w in suggest_scroll.winfo_children():
                w.destroy()
            
            if not query:
                return

            recipes = data_manager.load_json('recipes')
            matches = [s for s in sorted(recipes.keys()) if query in s.lower()][:10]
            
            for s in matches:
                ctk.CTkButton(
                    suggest_scroll, text=s, fg_color="transparent", 
                    height=28, anchor="w", text_color="#ecf0f1",
                    hover_color="#2c3e50",
                    command=lambda v=s: sku_entry.internal_var.set(v)
                ).pack(fill="x", padx=5)

        sku_entry.bind_search(on_search_update)

        # --- 3. ПОЛЕ КОЛИЧЕСТВА (ЖЕСТКО ЗАКРЕПЛЕНО НИЖЕ) ---
        ctk.CTkLabel(window, text="КОЛИЧЕСТВО:", font=("Arial", 11, "bold")).pack(pady=(10, 0))
        qty_entry = OrdoEntry(window, width=300, height=36, placeholder_text="1")
        qty_entry.pack(pady=5)

        def confirm_manual():
            sku = sku_entry.internal_var.get().strip()
            qty_s = qty_entry.get().strip()
            
            if not sku or not qty_s.isdigit():
                messagebox.showerror("Ошибка", "Заполните данные корректно", parent=window)
                return

            res = warehouse_service.add_order(sku, int(qty_s))
            if res["status"] == "success":
                messagebox.showinfo("Успех", res["message"])
                window.destroy()
                self._refresh_ui(res.get("updated_inventory"))
            else:
                messagebox.showerror("Ошибка", res["message"], parent=window)

        # Кнопка в самом низу
        ctk.CTkButton(
            window, text="✅ ОТГРУЗИТЬ ТОЧЕЧНО",
            fg_color="#3498db", height=50, width=250, font=("Arial", 12, "bold"),
            command=confirm_manual
        ).pack(pady=20)

    def _process_excel_immediately(self, window):
        path = filedialog.askopenfilename(
            filetypes=[("Excel/CSV", "*.xlsx *.csv")], 
            title="Выберите файл заказов",
            parent=window
        )
        if not path: return 

        try:
            res = warehouse_service.process_morning_orders(path)
            if res["status"] == "success":
                processed = res.get('processed', 0)
                errors = res.get('errors', [])
                window.destroy()
                if errors:
                    messagebox.showwarning("Результат", f"Обработано {processed} шт.\n\nДЕФИЦИТ:\n" + "\n".join(errors[:10]))
                else:
                    messagebox.showinfo("Успех", f"Файл обработан!\nВсего: {processed} шт.")
                self._refresh_ui(res.get("updated_inventory"))
            else:
                messagebox.showerror("Ошибка файла", res["message"], parent=window)
        except Exception as e:
            messagebox.showerror("Сбой", f"Ошибка при чтении файла: {e}", parent=window)

    def _refresh_ui(self, updated_data):
        view = getattr(self.parent, "current_view", None)
        if not view: return
        if updated_data and hasattr(view, 'update_rows'):
            view.update_rows(updated_data)
        elif hasattr(view, 'full_reload_and_refresh'):
            view.full_reload_and_refresh()