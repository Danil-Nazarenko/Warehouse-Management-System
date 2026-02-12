import data_manager
import pandas as pd

def report_defect(sku, amount, force=False):
    inventory = data_manager.load_json('inventory')
    sku = sku.strip()
    
    if sku not in inventory:
        return {"status": "error", "message": f"Товара '{sku}' нет на остатках."}

    if amount > inventory[sku] and not force:
        return {
            "status": "confirm_needed", 
            "message": f"На складе всего {inventory[sku]} шт. Списать {amount} шт. и уйти в минус?"
        }

    inventory[sku] -= amount
    data_manager.save_json('inventory', inventory)
    return {"status": "success", "message": f"Брак по {sku} списан."}

def process_excel_waste(file_path):
    """Логика чтения Excel для брака"""
    try:
        df = pd.read_excel(file_path)
        count = 0
        for _, row in df.iterrows():
            sku = str(row.iloc[0]).strip()
            qty = int(row.iloc[1])
            # Списываем принудительно (force=True), чтобы не прерывать цикл
            report_defect(sku, qty, force=True)
            count += 1
        return {"status": "success", "count": count}
    except Exception as e:
        return {"status": "error", "message": f"Ошибка парсинга: {e}"}