import json
import os
import sys

def get_base_path():
    """Определяет путь к папке, где лежит EXE или запущен скрипт."""
    # Если программа упакована PyInstaller-ом
    if getattr(sys, 'frozen', False):
        # Берем путь к папке, в которой лежит сам .exe
        return os.path.dirname(sys.executable)
    # Если запускаем как обычный .py
    return os.path.dirname(os.path.abspath(__file__))

# Базовая директория — это папка, где "живет" программа
BASE_DIR = get_base_path()

# Теперь FILES строит пути относительно папки запуска
FILES = {
    'inventory': os.path.join(BASE_DIR, 'inventory.json'),
    'recipes': os.path.join(BASE_DIR, 'recipes.json'),
    'recent_300': os.path.join(BASE_DIR, 'recent_300.json')
}

def load_json(key):
    """Загружает данные из JSON файла по ключу."""
    filename = FILES.get(key)
    if not filename:
        return {}
        
    if not os.path.exists(filename):
        # Если файла нет (первый запуск у директора), возвращаем пустую структуру
        return [] if key == 'recent_300' else {}
        
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка чтения {filename}: {e}")
        return [] if key == 'recent_300' else {}

def save_json(key, data):
    """Сохраняет данные в JSON файл."""
    filename = FILES.get(key)
    if filename:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

def update_recent_300(skus):
    """Обновляет список из 300 последних активных товаров."""
    if isinstance(skus, str):
        skus = [skus]

    recent = load_json('recent_300')
    if not isinstance(recent, list):
        recent = []

    inventory = load_json('inventory')

    for sku in skus:
        if not sku or str(sku).lower() == 'nan':
            continue
            
        if sku in inventory:
            if sku in recent:
                recent.remove(sku)
            recent.insert(0, sku)

    recent = recent[:300]
    save_json('recent_300', recent)