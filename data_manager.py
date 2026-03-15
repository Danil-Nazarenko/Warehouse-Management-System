import json
import os
import sys
import database
from datetime import datetime

def get_base_path():
    """Определяет путь к папке, где лежит EXE или запущен скрипт."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_path()
DB_PATH = os.path.join(BASE_DIR, 'ordo_v2.db')

# --- СОВМЕСТИМОСТЬ СО СТАРЫМ КОДОМ ---

def load_json(key):
    """Имитирует загрузку JSON, забирая данные из SQLite."""
    try:
        if key == 'inventory':
            return _db_load_inventory()
        elif key in ('recipes', 'catalog'):
            return _db_load_recipes()
        elif key == 'recent_300':
            return _db_load_recent()
        elif key == 'history':
            return _db_load_history()
    except Exception as e:
        print(f"Ошибка получения данных {key} из базы: {e}")
    
    return [] if key == 'recent_300' else {}

def save_json(key, data):
    """Имитирует сохранение JSON с использованием массовых операций."""
    try:
        if key == 'inventory':
            _db_sync_inventory(data)
        elif key in ('recipes', 'catalog'):
            _db_sync_recipes(data)
        elif key == 'recent_300':
            _db_save_recent(data)
    except Exception as e:
        print(f"Ошибка сохранения данных {key} в базу: {e}")

# --- ФУНКЦИИ УДАЛЕНИЯ ---

def delete_item_from_inventory(sku):
    """Точечное удаление товара из склада."""
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM inventory WHERE sku = ?', (sku,))
    conn.commit()
    conn.close()

def delete_item_from_catalog(sku):
    """Точечное удаление набора из каталога."""
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM recipes WHERE sku = ?', (sku,))
    conn.commit()
    conn.close()

# --- ВНУТРЕННИЕ ФУНКЦИИ РАБОТЫ С БД (ОПТИМИЗИРОВАННЫЕ) ---

def _db_load_inventory():
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT sku, quantity FROM inventory')
    data = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    return data

def _db_sync_inventory(data):
    """Массовая синхронизация склада."""
    conn = database.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('BEGIN TRANSACTION')
        
        # Удаление лишних
        cursor.execute('SELECT sku FROM inventory')
        db_skus = {row[0] for row in cursor.fetchall()}
        to_delete = [(sku,) for sku in (db_skus - set(data.keys()))]
        if to_delete:
            cursor.executemany('DELETE FROM inventory WHERE sku = ?', to_delete)
        
        # Массовое обновление/вставка
        to_update = list(data.items())
        if to_update:
            cursor.executemany('INSERT OR REPLACE INTO inventory (sku, quantity) VALUES (?, ?)', to_update)
            
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def _db_load_recipes():
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT sku, content FROM recipes')
    data = {row[0]: json.loads(row[1]) for row in cursor.fetchall()}
    conn.close()
    return data

def _db_sync_recipes(data):
    """Массовая синхронизация рецептов."""
    conn = database.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('BEGIN TRANSACTION')
        
        cursor.execute('SELECT sku FROM recipes')
        db_skus = {row[0] for row in cursor.fetchall()}
        to_delete = [(sku,) for sku in (db_skus - set(data.keys()))]
        if to_delete:
            cursor.executemany('DELETE FROM recipes WHERE sku = ?', to_delete)
        
        # Подготовка данных: SKU и JSON-строка контента
        to_update = [(sku, json.dumps(content)) for sku, content in data.items()]
        if to_update:
            cursor.executemany('INSERT OR REPLACE INTO recipes (sku, content) VALUES (?, ?)', to_update)
            
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def _db_load_recent():
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT sku FROM recent_items ORDER BY last_used DESC LIMIT 300')
    data = [row[0] for row in cursor.fetchall()]
    conn.close()
    return data

def _db_save_recent(skus):
    """Массовое сохранение недавних товаров."""
    conn = database.get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    try:
        cursor.execute('BEGIN TRANSACTION')
        to_save = [(sku, now) for sku in skus]
        cursor.executemany('INSERT OR REPLACE INTO recent_items (sku, last_used) VALUES (?, ?)', to_save)
        conn.commit()
    except:
        conn.rollback()
    finally:
        conn.close()

def _db_load_history():
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT date, filename, status, details FROM history ORDER BY id DESC')
    result = []
    for row in cursor.fetchall():
        result.append({
            'date': row[0],
            'filename': row[1],
            'status': row[2],
            'details': json.loads(row[3])
        })
    conn.close()
    return result

def update_recent_300(skus):
    """Оптимизированное обновление списка последних товаров."""
    if isinstance(skus, str):
        skus = [skus]
    
    conn = database.get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    try:
        cursor.execute('BEGIN TRANSACTION')
        # Фильтруем только те SKU, что есть в инвентаре
        placeholders = ','.join(['?'] * len(skus))
        cursor.execute(f'SELECT sku FROM inventory WHERE sku IN ({placeholders})', skus)
        existing_skus = [row[0] for row in cursor.fetchall()]
        
        if existing_skus:
            to_update = [(sku, now) for sku in existing_skus]
            cursor.executemany('INSERT OR REPLACE INTO recent_items (sku, last_used) VALUES (?, ?)', to_update)
        
        conn.commit()
    except:
        conn.rollback()
    finally:
        conn.close()