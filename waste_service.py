import data_manager
import pandas as pd

def report_defect(sku, amount, force=False):
    """Списание брака через SQL с возвратом нового остатка. Разрешен уход в минус."""
    inventory = data_manager.load_json('inventory')
    sku = sku.strip()

    current_qty = inventory.get(sku, 0)

    new_qty = current_qty - amount

    data_manager.update_inventory_batch({sku: new_qty})
    data_manager.update_recent_300([sku])
    
    return {
        "status": "success", 
        "message": f"Брак по {sku} списан. Остаток: {new_qty}",
        "updated_inventory": {sku: new_qty}
    }

def process_excel_waste(file_path):
    """Массовое списание брака из Excel. Обновляет даже те SKU, которых нет в базе."""
    try:
        # Читаем Excel (первая колонка - SKU, вторая - Кол-во)
        df = pd.read_excel(file_path, header=None) 
        count = 0
        all_updates = {} 
        
        inventory = data_manager.load_json('inventory')
        
        for _, row in df.iterrows():
            try:
                sku = str(row.iloc[0]).strip()
                qty = int(float(str(row.iloc[1]).replace(',', '.')))

                current = inventory.get(sku, 0)
                inventory[sku] = current - qty
                all_updates[sku] = inventory[sku]
                count += 1
            except:
                continue

        if all_updates:
            data_manager.update_inventory_batch(all_updates)
            data_manager.update_recent_300(list(all_updates.keys()))
                
        return {
            "status": "success", 
            "count": count, 
            "updated_inventory": all_updates 
        }
    except Exception as e:
        return {"status": "error", "message": f"Ошибка парсинга: {e}"}