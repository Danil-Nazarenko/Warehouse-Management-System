import data_manager
import pandas as pd

def get_all_items():
    """Загружает весь каталог (артикулы и их составы)"""
    return data_manager.load_json('recipes')

def get_item_content(sku):
    """Возвращает состав артикула. Если там "SIMPLE" или строка — возвращает {}."""
    catalog = data_manager.load_json('recipes')
    item = catalog.get(sku, {})
    
    if isinstance(item, str):
        return {}
    
    return item.copy() if isinstance(item, dict) else {}

def save_item(sku, content):
    """
    Сохраняет артикул. 
    Одиночные товары (content={}) попадают в каталог как "SIMPLE" и в инвентарь.
    Наборы (content={...}) попадают только в каталог.
    """
    try:
        sku_stripped = sku.strip()
        catalog = data_manager.load_json('recipes')
        
        # 1. ОПРЕДЕЛЯЕМ ТИП ТОВАРА
        is_kit = bool(content) # Если словарь состава не пустой — это набор
        final_value = content if is_kit else "SIMPLE"
        
        # 2. СОХРАНЯЕМ В КАТАЛОГ (всегда)
        catalog[sku_stripped] = final_value
        data_manager.save_json('recipes', catalog)
        print(f"DEBUG: {sku_stripped} сохранен в каталог как {'НАБОР' if is_kit else 'SIMPLE'}")

        # 3. РАБОТА С ИНВЕНТАРЕМ
        inventory = data_manager.load_json('inventory')
        
        if not is_kit:
            # Если это одиночный товар, и его нет в инвентаре — добавляем
            if sku_stripped not in inventory:
                inventory[sku_stripped] = 0
                data_manager.save_json('inventory', inventory)
                print(f"DEBUG: Одиночный товар {sku_stripped} добавлен на склад")
        else:
            # Если мы превратили старый одиночный товар в набор — удаляем его из инвентаря
            if sku_stripped in inventory:
                del inventory[sku_stripped]
                data_manager.save_json('inventory', inventory)
                print(f"DEBUG: {sku_stripped} стал набором и удален из списка остатков склада")
            
        return {"status": "success"}
    except Exception as e:
        print(f"DEBUG: Ошибка при сохранении: {e}")
        return {"status": "error", "message": str(e)}

def delete_item(sku):
    """Полное удаление артикула из всей системы"""
    try:
        # Удаляем из каталога
        catalog = data_manager.load_json('recipes')
        if sku in catalog:
            del catalog[sku]
            data_manager.save_json('recipes', catalog)

        # Удаляем из инвентаря (если он там был)
        inventory = data_manager.load_json('inventory')
        if sku in inventory:
            del inventory[sku]
            data_manager.save_json('inventory', inventory)
            
        return True
    except Exception as e:
        print(f"DEBUG: Ошибка при удалении: {e}")
        return False

def process_catalog_excel(file_path):
    """Массовый импорт одиночных товаров (всегда SIMPLE и всегда в инвентарь)"""
    try:
        df = pd.read_excel(file_path, header=None)
        catalog = data_manager.load_json('recipes')
        inventory = data_manager.load_json('inventory')
        count = 0
        
        for _, row in df.iterrows():
            raw_sku = str(row.iloc[0]).strip()
            if raw_sku and raw_sku.lower() != "nan" and raw_sku != "":
                # Для Excel-импорта мы по умолчанию считаем всё одиночными запчастями
                if raw_sku not in catalog:
                    catalog[raw_sku] = "SIMPLE"
                if raw_sku not in inventory:
                    inventory[raw_sku] = 0
                    count += 1
                    
        data_manager.save_json('recipes', catalog)
        data_manager.save_json('inventory', inventory)
        return {"status": "success", "count": count}
    except Exception as e:
        print(f"DEBUG: Ошибка Excel: {e}")
        return {"status": "error", "message": str(e)}