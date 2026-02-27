import pandas as pd
import data_manager

def process_morning_orders(filename):
    """Парсит 'шахматный' отчет (блоки по 3 столбца) и списывает остатки."""
    recipes = data_manager.load_json('recipes')
    inventory = data_manager.load_json('inventory')
    
    try:
        # Читаем файл БЕЗ заголовков (header=None), чтобы не потерять первую строку
        df = pd.read_excel(filename, header=None) if filename.endswith('.xlsx') else pd.read_csv(filename, header=None)
    except Exception as e:
        print(f"❌ Ошибка открытия файла: {e}")
        return

    print(f"\n--- Анализ структуры файла {filename} ---")
    
    # Собираем все заказы в один плоский список [(sku, qty), (sku, qty)...]
    extracted_orders = []
    
    # Итерируемся по столбцам с шагом 4 (пропускаем пустой, берем SKU, берем QTY, пропускаем разделитель)
    # Судя по твоему описанию: 0-пусто, 1-SKU, 2-QTY, 3-разделитель...
    for col_idx in range(0, df.shape[1], 4):
        # Проверяем, не вышли ли мы за пределы таблицы
        if col_idx + 2 < df.shape[1]:
            block = df.iloc[:, [col_idx + 1, col_idx + 2]] # Берем столбец артикула и кол-ва
            # Очищаем от пустых строк в этом блоке
            block = block.dropna()
            
            for _, row in block.iterrows():
                sku = str(row.iloc[0]).strip()
                try:
                    qty = int(row.iloc[1])
                    if sku and sku != 'nan' and sku != 'Артикул': # Игнорируем мусор
                        extracted_orders.append((sku, qty))
                except (ValueError, TypeError):
                    continue

    if not extracted_orders:
        print("❌ Не удалось извлечь ни одного заказа. Проверьте формат файла.")
        return

    print(f"Найдено позиций в файле: {len(extracted_orders)}")

    # --- ЛОГИКА СПИСАНИЯ (уже знакомая нам) ---
    processed_count = 0
    for order_sku, order_qty in extracted_orders:
        if order_sku not in recipes:
            print(f"⚠️ Артикул '{order_sku}' не найден в рецептах (Пропущен)")
            continue

        recipe = recipes[order_sku]
        items_to_deduct = {}

        if recipe == "SIMPLE":
            items_to_deduct = {order_sku: order_qty}
        elif isinstance(recipe, dict):
            for comp_sku, comp_qty in recipe.items():
                items_to_deduct[comp_sku] = comp_qty * order_qty

        # Проверка и вычитание
        can_fulfill = True
        for item, q_needed in items_to_deduct.items():
            if inventory.get(item, 0) < q_needed:
                can_fulfill = False
                print(f"🔴 ДЕФИЦИТ: '{order_sku}' (x{order_qty}) -> нет '{item}'")
                break
        
        if can_fulfill:
            for item, q_needed in items_to_deduct.items():
                inventory[item] -= q_needed
            processed_count += order_qty
            print(f"✅ Списано: {order_sku} ({order_qty} шт.)")

    data_manager.save_json('inventory', inventory)
    print(f"\n--- Итог: успешно обработано {processed_count} единиц товара ---")

def swap_items(sku_to_add, sku_to_remove, qty=1):
    """
    Проводит рокировку:
    1. Возвращает sku_to_add на склад (+qty)
    2. Списывает sku_to_remove со склада (-qty)
    """
    inventory = data_manager.load_json('inventory')
    
    # Проверка на наличие артикулов
    if sku_to_add not in inventory or sku_to_remove not in inventory:
        return {"status": "error", "message": "Один из артикулов не найден в базе"}

    if inventory[sku_to_remove] < qty:
        return {"status": "error", "message": f"Недостаточно '{sku_to_remove}' для списания"}

    inventory[sku_to_add] += qty
    inventory[sku_to_remove] -= qty
    
    data_manager.save_json('inventory', inventory)
    return {"status": "success"}

def get_all_skus():
    """Возвращает просто список всех артикулов для поиска"""
    inventory = data_manager.load_json('inventory')
    return list(inventory.keys())