import json
import os
import sys
import database
import sqlite3
from datetime import datetime

def get_base_path():
    """Определяет путь к папке, где лежит EXE или запущен скрипт."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_path()
DB_PATH = os.path.join(BASE_DIR, 'ordo_v2.db')

# --- ПРЯМАЯ РАБОТА С SQL ---

def load_json(key):
    """Быстрая загрузка данных через SQL. Поддерживает все ключи приложения."""
    conn = database.get_connection()
    cursor = conn.cursor()
    try:
        if key == 'inventory':
            cursor.execute('SELECT sku, quantity FROM inventory')
            return {row[0]: row[1] for row in cursor.fetchall()}
        
        elif key in ('recipes', 'catalog'):
            cursor.execute('SELECT sku, content FROM recipes')
            data = {}
            for row in cursor.fetchall():
                try:
                    data[row[0]] = json.loads(row[1])
                except (json.JSONDecodeError, TypeError):
                    data[row[0]] = row[1]
            return data
        
        elif key == 'recent_300':
            cursor.execute('SELECT sku FROM recent_items ORDER BY last_used DESC LIMIT 300')
            return [row[0] for row in cursor.fetchall()]
        
        elif key == 'history':
            cursor.execute('SELECT date, filename, status, details FROM history ORDER BY id DESC')
            return [{'date': r[0], 'filename': r[1], 'status': r[2], 'details': json.loads(r[3])} for r in cursor.fetchall()]
    except Exception as e:
        print(f"SQL Load Error ({key}): {e}")
    finally:
        conn.close()
    return {}

def get_active_skus_since(cutoff_date_str):
    """Возвращает уникальный список SKU, активных с указанной даты (SQL-оптимизация)."""
    conn = database.get_connection()
    cursor = conn.cursor()
    active_skus = set()
    try:
        # Запрашиваем только колонку details и только для нужных дат
        cursor.execute('SELECT details FROM history WHERE date >= ?', (cutoff_date_str,))
        
        for row in cursor.fetchall():
            try:
                details = json.loads(row[0])
                # Собираем артикулы из ключей словарей "Было" и "Изменения"
                if isinstance(details, dict):
                    active_skus.update(details.get('Было', {}).keys())
                    active_skus.update(details.get('Изменения', {}).keys())
            except:
                continue
        return list(active_skus)
    except Exception as e:
        print(f"SQL Active SKUs Error: {e}")
        return []
    finally:
        conn.close()

def update_inventory_batch(updates):
    """Пакетное обновление инвентаря."""
    if not updates: return
    conn = database.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('BEGIN TRANSACTION')
        data_to_update = [(sku, qty) for sku, qty in updates.items()]
        cursor.executemany('INSERT OR REPLACE INTO inventory (sku, quantity) VALUES (?, ?)', data_to_update)
        conn.commit()
    except Exception as e:
        if conn: conn.rollback()
        print(f"Ошибка SQL Inventory Batch: {e}")
    finally:
        conn.close()

def update_recipes_batch(updates):
    """Пакетное обновление рецептов."""
    if not updates: return
    conn = database.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('BEGIN TRANSACTION')
        data_to_update = []
        for sku, content in updates.items():
            val = json.dumps(content) if isinstance(content, dict) else content
            data_to_update.append((sku, val))
        cursor.executemany('INSERT OR REPLACE INTO recipes (sku, content) VALUES (?, ?)', data_to_update)
        conn.commit()
    except Exception as e:
        if conn: conn.rollback()
        print(f"Ошибка SQL Recipes Batch: {e}")
    finally:
        conn.close()

def add_history_record(filename, status, details):
    """Запись в историю с лимитом 400 записей."""
    conn = database.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('BEGIN TRANSACTION')
        cursor.execute('''
            INSERT INTO history (date, filename, status, details)
            VALUES (?, ?, ?, ?)
        ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), filename, status, json.dumps(details)))
        
        cursor.execute('''
            DELETE FROM history 
            WHERE id NOT IN (
                SELECT id FROM history 
                ORDER BY id DESC 
                LIMIT 400
            )
        ''')
        conn.commit()
    except Exception as e:
        if conn: conn.rollback()
        print(f"Ошибка при записи истории: {e}")
    finally:
        conn.close()

def delete_inventory_item(sku):
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM inventory WHERE sku = ?', (sku,))
    conn.commit()
    conn.close()

def delete_recipe_item(sku):
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM recipes WHERE sku = ?', (sku,))
    conn.commit()
    conn.close()

def clear_empty_history():
    conn = database.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM history WHERE details = '{}' OR details IS NULL OR details = ''")
        conn.commit()
    except Exception as e:
        print(f"Ошибка очистки истории: {e}")
    finally:
        conn.close()

def update_recent_300(skus):
    if not skus: return
    if isinstance(skus, str): skus = [skus]
    conn = database.get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    try:
        cursor.execute('BEGIN TRANSACTION')
        to_update = [(sku, now) for sku in skus]
        cursor.executemany('INSERT OR REPLACE INTO recent_items (sku, last_used) VALUES (?, ?)', to_update)
        conn.commit()
    except:
        if conn: conn.rollback()
    finally:
        conn.close()