import pandas as pd
import data_manager
from tkinter import filedialog
from datetime import datetime
import os
import json

def get_all_skus():
    """Возвращает отсортированный список всех SKU из каталога (таблица recipes)."""
    try:
        recipes = data_manager.load_json('recipes')
        if not recipes:
            return []
        return sorted(list(recipes.keys()))
    except Exception as e:
        print(f"Ошибка получения списка SKU для интерфейса: {e}")
        return []

def undo_last_action():
    """
    Восстанавливает состояние склада 'До', используя последнюю запись в истории.
    """
    try:
        history = data_manager.load_json('history')
        if not history:
            return {"status": "error", "message": "История пуста, нечего отменять."}

        last_record = history[0] 
        details = last_record.get("details", {})

        old_stocks = details.get("Было") 

        if not old_stocks:
            return {"status": "error", "message": "В последней записи нет данных 'Было' для отката."}

        data_manager.update_inventory_batch(old_stocks)

        data_manager.update_recent_300(list(old_stocks.keys()))

        if hasattr(data_manager, 'delete_last_history_record'):
            data_manager.delete_last_history_record()
        else:
            history.pop(0)
            data_manager.save_json('history', history)

        return {
            "status": "success",
            "message": f"Действие '{last_record.get('filename', 'Неизвестно')}' успешно отменено.",
            "updated_inventory": old_stocks
        }
    except Exception as e:
        return {"status": "error", "message": f"Ошибка при откате: {e}"}

def add_order(sku, qty):
    """
    Точечная отгрузка товара или набора.
    Учитывает составы из recipes.
    """
    try:
        inventory = data_manager.load_json('inventory')
        recipes = data_manager.load_json('recipes')
        sku = sku.strip()
        
        updated_items = {}
        old_stocks = {}

        if sku in recipes:
            recipe = recipes[sku]
            items_to_deduct = {sku: qty} if recipe == "SIMPLE" else {k: v * qty for k, v in recipe.items()}
        else:
            items_to_deduct = {sku: qty}

        for item_sku, q_needed in items_to_deduct.items():
            old_val = inventory.get(item_sku, 0)
            new_val = old_val - q_needed
            
            old_stocks[item_sku] = old_val
            updated_items[item_sku] = new_val

        data_manager.update_inventory_batch(updated_items)
        data_manager.update_recent_300(list(updated_items.keys()))

        is_deficit = any(v < 0 for v in updated_items.values())
        data_manager.add_history_record(
            filename=f"Отгрузка: {sku}",
            status="Дефицит" if is_deficit else "Готово",
            details={
                "Изменения": updated_items, 
                "Было": old_stocks, 
                "тип": "отгрузка",
                "кол-во": qty
            }
        )
        
        return {
            "status": "success",
            "message": f"Отгружено: {sku} (x{qty})",
            "updated_inventory": updated_items
        }
    except Exception as e:
        return {"status": "error", "message": f"Ошибка отгрузки: {e}"}

def swap_items(sku_from, sku_to, qty):
    try:
        inventory = data_manager.load_json('inventory')
        sku_from = sku_from.strip()
        sku_to = sku_to.strip()
        
        if sku_from == sku_to:
            return {"status": "error", "message": "Выбраны одинаковые артикулы."}
            
        old_from = inventory.get(sku_from, 0)
        old_to = inventory.get(sku_to, 0)
        
        new_qty_from = old_from - qty
        new_qty_to = old_to + qty
        
        updates = {sku_from: new_qty_from, sku_to: new_qty_to}
        old_stocks = {sku_from: old_from, sku_to: old_to}
        
        data_manager.update_inventory_batch(updates)
        data_manager.update_recent_300(list(updates.keys()))

        data_manager.add_history_record(
            filename="Ручная замена",
            status="Успех",
            details={"Изменения": updates, "Было": old_stocks, "тип": "замена"}
        )
        
        return {
            "status": "success", 
            "message": f"Замена выполнена:\n{sku_from} ({new_qty_from})\n{sku_to} ({new_qty_to})",
            "updated_inventory": updates 
        }
    except Exception as e:
        return {"status": "error", "message": f"Ошибка замены: {str(e)}"}

def add_supply(sku, qty):
    try:
        inventory = data_manager.load_json('inventory')
        sku = sku.strip()
        
        old_qty = inventory.get(sku, 0) 
        new_qty = old_qty + qty
        
        updates = {sku: new_qty}
        old_stocks = {sku: old_qty}
        
        data_manager.update_inventory_batch(updates)
        data_manager.update_recent_300([sku])

        data_manager.add_history_record(
            filename="Ручной приход",
            status="Успех",
            details={"Изменения": updates, "Было": old_stocks, "тип": "приход"}
        )
        
        return {
            "status": "success",
            "message": f"Принято: {sku} (+{qty})",
            "updated_inventory": updates
        }
    except Exception as e:
        return {"status": "error", "message": f"Ошибка прихода: {e}"}

def report_defect(sku, qty):
    try:
        inventory = data_manager.load_json('inventory')
        sku = sku.strip()
        
        old_qty = inventory.get(sku, 0) 
        new_qty = old_qty - qty
        
        updates = {sku: new_qty}
        old_stocks = {sku: old_qty}
        
        data_manager.update_inventory_batch(updates)
        data_manager.update_recent_300([sku])

        data_manager.add_history_record(
            filename="Списание брака",
            status="Дефицит" if new_qty < 0 else "Успех",
            details={"Изменения": updates, "Было": old_stocks, "тип": "брак"}
        )
        
        return {
            "status": "success",
            "message": f"Списан брак: {sku} (Остаток: {new_qty})",
            "updated_inventory": updates
        }
    except Exception as e:
        return {"status": "error", "message": f"Ошибка списания: {e}"}

def process_morning_orders(filename):
    recipes = data_manager.load_json('recipes')
    inventory = data_manager.load_json('inventory')
    
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
    old_stocks = {} 

    current_inv_state = inventory.copy()

    for order_sku, total_qty in total_file_demands.items():
        if order_sku not in recipes:
            errors.append(f"Ошибка: '{order_sku}' отсутствует в КАТАЛОГЕ")
            continue

        recipe = recipes[order_sku]
        items_to_deduct = {order_sku: total_qty} if recipe == "SIMPLE" else {k: v * total_qty for k, v in recipe.items()}

        for item, q_needed in items_to_deduct.items():
            if item not in old_stocks:
                old_stocks[item] = current_inv_state.get(item, 0)
                
            current_stock = current_inv_state.get(item, 0)
            new_stock = current_stock - q_needed
            
            current_inv_state[item] = new_stock
            updated_items[item] = new_stock
            
            if new_stock < 0:
                errors.append(f"Дефицит: '{item}' (остаток: {new_stock})")
        
        processed_count += total_qty

    if updated_items:
        data_manager.update_inventory_batch(updated_items)
        data_manager.update_recent_300(list(updated_items.keys()))
        
        history_details = {
            "Было": old_stocks,
            "Изменения": updated_items, 
            "статистика": {
                "позиций": len(total_file_demands),
                "всего_шт": processed_count,
                "ошибки": len([e for e in errors if "отсутствует" in e])
            }
        }

        data_manager.add_history_record(
            filename=f"Заказы: {os.path.basename(filename)}",
            status="Готово" if not errors else "Дефицит",
            details=history_details
        )
    
    return {
        "status": "success", 
        "processed": processed_count,
        "errors_count": len(errors),
        "updated_inventory": updated_items,
        "errors": errors 
    }

def export_inventory_to_excel():
    try:
        inventory = data_manager.load_json('inventory')
        if not inventory:
            return {"status": "error", "message": "Склад пуст, нечего экспортировать."}
        data = [{"Артикул": sku, "Остаток": qty} for sku, qty in sorted(inventory.items())]
        df = pd.DataFrame(data)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        default_filename = f"Остатки_склада_{timestamp}.xlsx"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            initialfile=default_filename,
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="Выберите куда сохранить остатки"
        )
        if not file_path:
            return {"status": "cancelled"}
        df.to_excel(file_path, index=False)
        return {"status": "success", "message": f"Файл успешно сохранен:\n{os.path.basename(file_path)}"}
    except Exception as e:
        return {"status": "error", "message": f"Ошибка при экспорте: {str(e)}"}