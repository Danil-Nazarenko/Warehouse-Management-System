import pandas as pd
import data_manager
from tkinter import filedialog
from datetime import datetime
import json

def export_inventory_to_excel():
    """Выгружает текущие остатки склада в файл Excel."""
    inventory = data_manager.load_json('inventory')
    
    if not inventory:
        return {"status": "error", "message": "Склад пуст, нечего выгружать"}

    try:
        data_list = [{"Артикул (SKU)": sku, "Остаток на складе": qty} 
                     for sku, qty in inventory.items()]
        
        df = pd.DataFrame(data_list).sort_values(by="Артикул (SKU)")

        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfile=f"Остатки_{datetime.now().strftime('%d_%m')}.xlsx",
            title="Сохранить отчет по складу"
        )

        if file_path:
            df.to_excel(file_path, index=False)
            return {"status": "success", "message": "Файл успешно сохранен"}
        
        return {"status": "cancel"}
    except Exception as e:
        return {"status": "error", "message": f"Ошибка при экспорте: {e}"}

def process_morning_orders(filename):
    """Парсит отчет и списывает остатки с записью в историю."""
    recipes = data_manager.load_json('recipes')
    inventory = data_manager.load_json('inventory')
    
    try:
        df = pd.read_excel(filename, header=None) if filename.endswith('.xlsx') else pd.read_csv(filename, header=None)
    except Exception as e:
        return {"status": "error", "message": f"Ошибка открытия файла: {e}"}

    extracted_orders = []
    # Шахматный парсинг (блоки по 4 столбца)
    for col_idx in range(0, df.shape[1], 4):
        if col_idx + 2 < df.shape[1]:
            block = df.iloc[:, [col_idx + 1, col_idx + 2]].dropna()
            for _, row in block.iterrows():
                sku = str(row.iloc[0]).strip()
                try:
                    qty = int(row.iloc[1])
                    if sku and sku.lower() != 'nan' and sku != 'Артикул':
                        extracted_orders.append((sku, qty))
                except: continue

    if not extracted_orders:
        return {"status": "error", "message": "Не удалось извлечь заказы. Проверьте формат."}

    processed_count = 0
    errors = []
    updated_skus_pool = set() # Используем set для уникальности

    for order_sku, order_qty in extracted_orders:
        if order_sku not in recipes:
            errors.append(f"Пропущен: {order_sku} (нет в каталоге)")
            continue

        recipe = recipes[order_sku]
        items_to_deduct = {order_sku: order_qty} if recipe == "SIMPLE" else {k: v * order_qty for k, v in recipe.items()}

        # Проверка дефицита
        can_fulfill = True
        for item, q_needed in items_to_deduct.items():
            if inventory.get(item, 0) < q_needed:
                can_fulfill = False
                errors.append(f"Дефицит: {item} для {order_sku}")
                break
        
        if can_fulfill:
            for item, q_needed in items_to_deduct.items():
                inventory[item] -= q_needed
                updated_skus_pool.add(item)
            processed_count += order_qty

    # --- СОХРАНЕНИЕ ---
    # 1. Склад (теперь через быструю транзакцию)
    data_manager.save_json('inventory', inventory)
    
    # 2. Обновление Топ-300 (только уникальные SKU)
    if updated_skus_pool:
        data_manager.update_recent_300(list(updated_skus_pool))

    # 3. Запись в историю (база данных ordo_v2 позволяет это легко делать)
    # Здесь мы можем напрямую вызвать сохранение в таблицу истории, если добавим метод в data_manager
    # Но пока просто вернем результат для GUI
    
    summary = {
        "processed": processed_count,
        "errors_count": len(errors),
        "details": errors[:10] # Первые 10 ошибок для лога
    }
    
    return {"status": "success", "data": summary}

def swap_items(sku_to_add, sku_to_remove, qty=1):
    """Рокировка товара на складе."""
    inventory = data_manager.load_json('inventory')
    
    if sku_to_add not in inventory or sku_to_remove not in inventory:
        return {"status": "error", "message": "Один из артикулов не найден"}

    if inventory[sku_to_remove] < qty:
        return {"status": "error", "message": f"Недостаточно '{sku_to_remove}'"}

    inventory[sku_to_add] += qty
    inventory[sku_to_remove] -= qty
    
    data_manager.save_json('inventory', inventory)
    data_manager.update_recent_300([sku_to_add, sku_to_remove])
    
    return {"status": "success"}

def get_all_skus():
    """Список всех артикулов для поиска."""
    return list(data_manager.load_json('inventory').keys())