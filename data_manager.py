import json
import os

FILES = {
    'inventory': 'inventory.json',  # Остатки
    'recipes': 'recipes.json'       # Состав комплектов
}

def load_json(key):
    """Загружает данные из JSON файла по ключу."""
    filename = FILES.get(key)
    if not filename:
        return {}
        
    if not os.path.exists(filename):
        return {}
        
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка чтения {filename}: {e}")
        return {}

def save_json(key, data):
    """Сохраняет данные в JSON файл."""
    filename = FILES.get(key)
    if filename:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)