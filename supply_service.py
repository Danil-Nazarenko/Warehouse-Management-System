import data_manager
import pandas as pd

def add_supply(sku, amount):
    """Ручная приемка товара через SQL."""
    inventory = data_manager.load_json('inventory')
    recipes = data_manager.load_json('recipes')
    
    sku = sku.strip()
    if sku not in recipes:
        return {"status": "not_in_catalog", "message": f"Артикул '{sku}' не найден в каталоге!"}

    try:
        current_qty = inventory.get(sku, 0)
        new_qty = current_qty + amount

        data_manager.update_inventory_batch({sku: new_qty})
        data_manager.update_recent_300([sku])
        
        return {
            "status": "success", 
            "message": f"Успешно! {sku}: {new_qty}",
            "updated_inventory": {sku: new_qty}
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def process_excel_supply(file_path):
    """Логика массового прихода из Excel с подготовкой данных для истории."""
    try:
        df = pd.read_excel(file_path, header=None) 
        count = 0
        all_updates = {}
        old_states = {}
        
        inventory = data_manager.load_json('inventory')
        recipes = data_manager.load_json('recipes')
        
        for _, row in df.iterrows():
            try:
                sku = str(row.iloc[0]).strip()
                if sku.endswith('.0'): sku = sku[:-2]
                
                qty_raw = str(row.iloc[1]).replace(',', '.')
                qty = int(float(qty_raw))
                
                if sku in recipes:
                    if sku not in old_states:
                        old_states[sku] = inventory.get(sku, 0)
                    
                    current = inventory.get(sku, 0)
                    new_val = current + qty
                    inventory[sku] = new_val
                    all_updates[sku] = new_val
                    count += 1
            except:
                continue

        if all_updates:
            data_manager.update_inventory_batch(all_updates)
            data_manager.update_recent_300(list(all_updates.keys()))
                
        return {
            "status": "success", 
            "count": count,
            "changes": all_updates,
            "old_inventory": old_states
        }
    except Exception as e:
        return {"status": "error", "message": f"Ошибка парсинга: {e}"}