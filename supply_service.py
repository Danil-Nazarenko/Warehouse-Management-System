import data_manager
import pandas as pd

def add_supply(sku, amount):
    inventory = data_manager.load_json('inventory')
    recipes = data_manager.load_json('recipes')
    
    sku = sku.strip()
    if sku not in recipes:
        return {"status": "not_in_catalog", "message": f"Артикул '{sku}' не найден в каталоге!"}

    try:
        if sku not in inventory:
            inventory[sku] = 0
        inventory[sku] += amount
        data_manager.save_json('inventory', inventory)
        return {"status": "success", "new_balance": inventory[sku], "message": f"Успешно! {sku}: {inventory[sku]}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def process_excel_supply(file_path):
    """Логика чтения Excel для прихода"""
    try:
        df = pd.read_excel(file_path)
        count = 0
        for _, row in df.iterrows():
            sku = str(row.iloc[0]).strip()
            qty = int(row.iloc[1])
            add_supply(sku, qty)
            count += 1
        return {"status": "success", "count": count}
    except Exception as e:
        return {"status": "error", "message": f"Ошибка парсинга: {e}"}