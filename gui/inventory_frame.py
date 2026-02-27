import customtkinter as ctk
import data_manager

class InventoryFrame(ctk.CTkFrame):
    def __init__(self, master, search_var, copy_func, **kwargs):
        super().__init__(master, **kwargs)
        self.search_var = search_var
        self.copy_to_clipboard = copy_func
        
        # Настройка UI
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(20, 10), padx=20)
        
        ctk.CTkLabel(header_frame, text="Склад", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")
        ctk.CTkEntry(header_frame, placeholder_text="🔍 Поиск...", width=300, textvariable=self.search_var).pack(side="right")
        
        self.scroll_frame = ctk.CTkScrollableFrame(self, width=800, height=500)
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.refresh()

    def manual_update_stock(self, sku, new_qty_str):
        if not new_qty_str.isdigit(): return
        inventory = data_manager.load_json('inventory')
        inventory[sku] = int(new_qty_str)
        data_manager.save_json('inventory', inventory)
        self.refresh()

    def refresh(self, *args):
        if not self.winfo_exists(): return
        search_query = self.search_var.get().lower()
        
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        inventory = data_manager.load_json('inventory')
        for sku in sorted(inventory.keys()):
            if search_query in sku.lower():
                qty = inventory[sku]
                card_color = "#3b1e1e" if qty < 5 else "#2b2b2b"
                row = ctk.CTkFrame(self.scroll_frame, fg_color=card_color, corner_radius=6)
                row.pack(fill="x", pady=2)
                
                ctk.CTkButton(row, text="📋", width=30, height=30, fg_color="transparent", 
                              command=lambda s=sku: self.copy_to_clipboard(s)).pack(side="left", padx=5)
                
                ctk.CTkLabel(row, text=sku, font=("Arial", 14), anchor="w").pack(side="left", padx=5, pady=10)
                
                edit_frame = ctk.CTkFrame(row, fg_color="transparent")
                edit_frame.pack(side="right", padx=10)
                
                qty_edit = ctk.CTkEntry(edit_frame, width=60, height=28, justify="center")
                qty_edit.insert(0, str(qty))
                qty_edit.pack(side="left", padx=5)
                
                ctk.CTkButton(edit_frame, text="💾", width=30, height=28, fg_color="#27ae60", 
                              command=lambda s=sku, e=qty_edit: self.manual_update_stock(s, e.get())).pack(side="left")