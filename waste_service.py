import data_manager
import pandas as pd

def report_defect(sku, amount, force=False):
    """Списание брака через SQL с возвратом нового остатка."""
    # Загружаем текущий срез из SQL
    inventory = data_manager.load_json('inventory')
    sku = sku.strip()
    
    if sku not in inventory:
        return {"status": "error", "message": f"Товара '{sku}' нет на остатках."}

    current_qty = inventory[sku]

    # Проверка на уход в минус (если не форсировано)
    if amount > current_qty and not force:
        return {
            "status": "confirm_needed", 
            "message": f"На складе всего {current_qty} шт. Списать {amount} шт. и уйти в минус?"
        }

    # Считаем новый остаток
    new_qty = current_qty - amount
    
    # ПИШЕМ В SQL (вместо save_json)
    data_manager.update_inventory_batch({sku: new_qty})
    data_manager.update_recent_300([sku])
    
    return {
        "status": "success", 
        "message": f"Брак по {sku} списан.",
        "sku": sku,
        "new_qty": new_qty
    }

def process_excel_waste(file_path):
    """Массовое списание брака из Excel с пакетным обновлением базы."""
    try:
        # Читаем Excel (первая колонка - SKU, вторая - Кол-во)
        df = pd.read_excel(file_path, header=None) 
        count = 0
        all_updates = {} # Сюда соберем все изменения для одного SQL запроса
        
        # Сначала собираем текущее состояние склада
        inventory = data_manager.load_json('inventory')
        
        for _, row in df.iterrows():
            try:
                sku = str(row.iloc[0]).strip()
                qty = int(float(str(row.iloc[1]).replace(',', '.')))
                
                if sku in inventory:
                    inventory[sku] -= qty
                    all_updates[sku] = inventory[sku]
                    count += 1
            except:
                continue
        
        # ОДИН пакетный запрос к базе для всех строк Excel
        if all_updates:
            data_manager.update_inventory_batch(all_updates)
            data_manager.update_recent_300(list(all_updates.keys()))
                
        return {
            "status": "success", 
            "count": count, 
            "updated_inventory": all_updates # Это пойдет в UI для обновления экрана
        }
    except Exception as e:
        return {"status": "error", "message": f"Ошибка парсинга: {e}"}