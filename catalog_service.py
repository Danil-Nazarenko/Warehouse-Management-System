import data_manager
import pandas as pd
import json

def get_all_items():
    """Загружает весь каталог (артикулы и их составы) из SQL."""
    return data_manager.load_json('recipes')

def get_item_content(sku):
    """Возвращает состав артикула."""
    catalog = data_manager.load_json('recipes')
    item = catalog.get(sku, {})
    
    # Если это строка (например "SIMPLE"), возвращаем пустой словарь состава
    if isinstance(item, str):
        return {}
    
    return item.copy() if isinstance(item, dict) else {}

def save_item(sku, content):
    """
    Сохраняет артикул в SQL.
    Одиночные товары (content={}) попадают в recipes как "SIMPLE" и добавляются в inventory.
    Наборы (content={...}) попадают только в recipes.
    """
    try:
        sku_stripped = sku.strip()
        
        # 1. ОПРЕДЕЛЯЕМ ТИП ТОВАРА
        is_kit = bool(content) 
        final_value = content if is_kit else "SIMPLE"
        
        # 2. СОХРАНЯЕМ В КАТАЛОГ (таблица recipes)
        # Мы передаем словарь из одного элемента в пакетный метод
        data_manager.update_recipes_batch({sku_stripped: final_value})
        
        # 3. РАБОТА С ИНВЕНТАРЕМ
        inventory = data_manager.load_json('inventory')
        
        if not is_kit:
            # Если это одиночный товар и его нет в инвентаре — создаем запись с 0
            if sku_stripped not in inventory:
                data_manager.update_inventory_batch({sku_stripped: 0})
        else:
            # Если превратили одиночный товар в набор — удаляем его из остатков склада
            if sku_stripped in inventory:
                data_manager.delete_inventory_item(sku_stripped)
            
        return {"status": "success"}
    except Exception as e:
        print(f"DEBUG: Ошибка при сохранении в SQL: {e}")
        return {"status": "error", "message": str(e)}

def delete_item(sku):
    """Полное удаление артикула из SQL таблиц recipes и inventory."""
    try:
        # Удаляем из обеих таблиц через методы data_manager
        data_manager.delete_recipe_item(sku)
        data_manager.delete_inventory_item(sku)
        return True
    except Exception as e:
        print(f"DEBUG: Ошибка при удалении из SQL: {e}")
        return False

def process_catalog_excel(file_path):
    """Массовый импорт новых товаров из Excel (всегда SIMPLE)."""
    try:
        df = pd.read_excel(file_path, header=None, dtype=str)
        
        # Загружаем текущее состояние для проверки на дубликаты
        catalog = data_manager.load_json('recipes')
        inventory = data_manager.load_json('inventory')
        
        new_recipes = {}
        new_inventory = {}
        count = 0
        
        for _, row in df.iterrows():
            val = row.iloc[0]
            if pd.isna(val): continue
                
            raw_sku = str(val).strip()
            if raw_sku.endswith('.0'): raw_sku = raw_sku[:-2]

            if raw_sku and raw_sku.lower() != "nan":
                is_new = False
                
                if raw_sku not in catalog:
                    new_recipes[raw_sku] = "SIMPLE"
                    is_new = True
                
                if raw_sku not in inventory:
                    new_inventory[raw_sku] = 0
                    is_new = True
                
                if is_new:
                    count += 1
                    
        # Пакетное сохранение в SQL
        if new_recipes:
            data_manager.update_recipes_batch(new_recipes)
        if new_inventory:
            data_manager.update_inventory_batch(new_inventory)
            
        print(f"DEBUG: SQL Импорт завершен. Новых позиций: {count}")
        return {"status": "success", "count": count}
    except Exception as e:
        print(f"DEBUG: Ошибка SQL Excel импорта: {e}")
        return {"status": "error", "message": str(e)}