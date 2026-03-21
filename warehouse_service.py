import pandas as pd
import data_manager
from tkinter import filedialog
from datetime import datetime
import json

def process_morning_orders(filename):
    """Обработка заказов с агрегацией и расширенной диагностикой."""
    recipes = data_manager.load_json('recipes')
    inventory = data_manager.load_json('inventory')
    
    # --- БЛОК ПРОВЕРКИ БАЗЫ ---
    print("\n" + "="*50)
    print(f"DIAGNOSTIC: Загружено из БД {len(inventory)} артикулов инвентаря.")
    print(f"DIAGNOSTIC: Загружено из БД {len(recipes)} рецептов/каталога.")
    if inventory:
        print(f"DIAGNOSTIC: Пример SKU в базе: '{list(inventory.keys())[0]}'")
    else:
        print("WARNING: БАЗА ИНВЕНТАРЯ ПУСТА!")
    print("="*50 + "\n")
    # --------------------------

    try:
        if filename.endswith('.xlsx'):
            df = pd.read_excel(filename, header=None, dtype=str)
        else:
            df = pd.read_csv(filename, header=None, dtype=str)
    except Exception as e:
        return {"status": "error", "message": f"Ошибка открытия файла: {e}"}

    total_file_demands = {}
    
    for col_idx in range(0, df.shape[1], 4):
        if col_idx + 2 < df.shape[1]:
            block = df.iloc[:, [col_idx + 1, col_idx + 2]].dropna()
            for _, row in block.iterrows():
                sku = str(row.iloc[0]).strip()
                if sku.endswith('.0'): sku = sku[:-2]
                try:
                    qty = int(float(str(row.iloc[1]).replace(',', '.')))
                    if sku and sku.lower() != 'nan' and sku != 'Артикул':
                        total_file_demands[sku] = total_file_demands.get(sku, 0) + qty
                except: continue

    if not total_file_demands:
        return {"status": "error", "message": "Не удалось найти заказы в файле."}

    processed_count = 0
    errors = []
    updated_items = {} 

    # 2. РАСЧЕТ
    for order_sku, total_qty in total_file_demands.items():
        # ПРОВЕРКА 1: Есть ли вообще такой артикул в каталоге?
        if order_sku not in recipes:
            err = f"Ошибка: '{order_sku}' отсутствует в КАТАЛОГЕ"
            errors.append(err)
            print(err)
            continue

        recipe = recipes[order_sku]
        items_to_deduct = {order_sku: total_qty} if recipe == "SIMPLE" else {k: v * total_qty for k, v in recipe.items()}

        can_fulfill = True
        for item, q_needed in items_to_deduct.items():
            # ПРОВЕРКА 2: Есть ли артикул в инвентаре и хватает ли остатка?
            current_stock = inventory.get(item)
            
            if current_stock is None:
                can_fulfill = False
                err = f"Дефицит: '{item}' НЕТ В ТАБЛИЦЕ ИНВЕНТАРЯ"
                errors.append(err)
                print(err)
                break
            
            if current_stock < q_needed:
                can_fulfill = False
                err = f"Дефицит: '{item}' (нужно {q_needed}, в базе {current_stock})"
                errors.append(err)
                print(err)
                break
        
        if can_fulfill:
            for item, q_needed in items_to_deduct.items():
                inventory[item] -= q_needed
                updated_items[item] = inventory[item]
            processed_count += total_qty

    # 3. ЗАПИСЬ
    if updated_items:
        data_manager.update_inventory_batch(updated_items)
        data_manager.update_recent_300(list(updated_items.keys()))
    
    print(f"\nИТОГ: Обработано {processed_count}, Ошибок: {len(errors)}")
    
    return {
        "status": "success", 
        "processed": processed_count,
        "errors_count": len(errors),
        "updated_inventory": updated_items 
    }