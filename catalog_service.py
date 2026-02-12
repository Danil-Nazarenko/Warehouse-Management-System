import data_manager
import pandas as pd

def get_all_items():
    """Загружает весь каталог (артикулы и их составы)"""
    return data_manager.load_json('recipes')

def get_item_content(sku):
    """Возвращает состав артикула. Если там "SIMPLE" или строка — возвращает {}."""
    catalog = data_manager.load_json('recipes')
    item = catalog.get(sku, {})
    
    # Если это одиночный товар (строка "SIMPLE" или старый формат названия)
    if isinstance(item, str):
        return {}
    
    # Возвращаем копию словаря (состав набора)
    return item.copy() if isinstance(item, dict) else {}

def save_item(sku, content):
    """Сохраняет артикул в каталог и инициализирует его в инвентаре"""
    try:
        sku_stripped = sku.strip()
        
        # 1. ОБНОВЛЕНИЕ КАТАЛОГА (recipes.json)
        catalog = data_manager.load_json('recipes')
        
        # Если словарь состава пустой — записываем "SIMPLE", иначе сам словарь
        final_value = content if content else "SIMPLE"
        
        catalog[sku_stripped] = final_value
        data_manager.save_json('recipes', catalog)
        print(f"DEBUG: {sku_stripped} сохранен в recipes как {final_value}")

        # 2. ОБНОВЛЕНИЕ СКЛАДА (inventory.json)
        inventory = data_manager.load_json('inventory')
        
        # Если товара еще нет на складе, создаем запись с 0
        if sku_stripped not in inventory:
            inventory[sku_stripped] = 0
            data_manager.save_json('inventory', inventory)
            print(f"DEBUG: {sku_stripped} инициализирован в inventory с остатком 0")
            
        return {"status": "success"}
    except Exception as e:
        print(f"DEBUG: Ошибка при сохранении: {e}")
        return {"status": "error", "message": str(e)}

def delete_item(sku):
    """Полное удаление артикула из системы (Каталог + Склад)"""
    try:
        # 1. Удаляем из каталога (recipes.json)
        catalog = data_manager.load_json('recipes')
        if sku in catalog:
            del catalog[sku]
            data_manager.save_json('recipes', catalog)
            print(f"DEBUG: {sku} удален из каталога (recipes.json)")

        # 2. Удаляем из инвентаря (inventory.json)
        inventory = data_manager.load_json('inventory')
        if sku in inventory:
            del inventory[sku]
            data_manager.save_json('inventory', inventory)
            print(f"DEBUG: {sku} удален из склада (inventory.json)")
            
        return True
    except Exception as e:
        print(f"DEBUG: Ошибка при удалении: {e}")
        return False

def process_catalog_excel(file_path):
    """Массовый импорт: добавляет товары в recipes как SIMPLE и создает их в inventory"""
    try:
        df = pd.read_excel(file_path, header=None)
        catalog = data_manager.load_json('recipes')
        inventory = data_manager.load_json('inventory')
        count = 0
        
        for _, row in df.iterrows():
            raw_sku = str(row.iloc[0]).strip()
            
            if raw_sku and raw_sku.lower() != "nan" and raw_sku != "":
                # Добавляем в рецепты как одиночный товар, если его там нет
                if raw_sku not in catalog:
                    catalog[raw_sku] = "SIMPLE"
                
                # Добавляем на склад с нулевым остатком, если его там нет
                if raw_sku not in inventory:
                    inventory[raw_sku] = 0
                    count += 1
                    
        data_manager.save_json('recipes', catalog)
        data_manager.save_json('inventory', inventory)
        return {"status": "success", "count": count}
    except Exception as e:
        print(f"DEBUG: Ошибка Excel: {e}")
        return {"status": "error", "message": str(e)}