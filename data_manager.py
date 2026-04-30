import json
import os
import sys
import database
import sqlite3
from datetime import datetime

def get_history_paginated(page, per_page=20):
    """
    Возвращает список записей для конкретной страницы с именами ключей, 
    совместимыми с HistoryView.
    """
    offset = (page - 1) * per_page
    # Используем database.get_connection, как в остальном файле
    conn = database.get_connection() 
    cursor = conn.cursor()
    
    # ВАЖНО: выбираем date как r[0], чтобы интерфейс его видел
    cursor.execute("""
        SELECT date, filename, status, details, id 
        FROM history 
        ORDER BY id DESC 
        LIMIT ? OFFSET ?
    """, (per_page, offset))
    
    rows = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(*) FROM history")
    total_records = cursor.fetchone()[0]
    conn.close()
    
    history = []
    for row in rows:
        history.append({
            "date": row[0],
            "filename": row[1],
            "status": row[2],
            "details": json.loads(row[3]) if row[3] else {},
            "id": row[4]
        })
        
    return history, total_records

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
            # Добавлена выборка id для корректной работы лимитов и поиска
            cursor.execute('SELECT date, filename, status, details, id FROM history ORDER BY id DESC')
            return [{'date': r[0], 'filename': r[1], 'status': r[2], 'details': json.loads(r[3]), 'id': r[4]} for r in cursor.fetchall()]
    except Exception as e:
        print(f"SQL Load Error ({key}): {e}")
    finally:
        conn.close()
    return {}

# --- НОВАЯ ФУНКЦИЯ ДЛЯ ОТКАТА ---
def delete_last_history_record():
    """Удаляет самую последнюю запись из таблицы истории."""
    conn = database.get_connection()
    cursor = conn.cursor()
    try:
        # Находим максимальный ID (последнюю запись) и удаляем её
        cursor.execute('DELETE FROM history WHERE id = (SELECT MAX(id) FROM history)')
        conn.commit()
    except Exception as e:
        if conn: conn.rollback()
        print(f"Ошибка удаления записи истории: {e}")
    finally:
        conn.close()

def get_active_skus_since(cutoff_date_str):
    """
    Возвращает словарь со статистикой по каждому SKU за период.
    Фиксирует начальное состояние из первой найденной записи и аккумулирует изменения.
    """
    conn = database.get_connection()
    cursor = conn.cursor()
    stats = {} # Структура: { 'sku': {'initial_was': 0, 'total_diff': 0} }
    
    try:
        cursor.execute('SELECT details FROM history WHERE date >= ? ORDER BY date ASC', (cutoff_date_str,))
        
        for row in cursor.fetchall():
            try:
                details = json.loads(row[0])
                if not isinstance(details, dict): continue
                
                was_map = details.get('Было', {})
                diff_map = details.get('Изменения', {})

                for sku, diff in diff_map.items():
                    if sku not in stats:
                        initial = was_map.get(sku, 0)
                        stats[sku] = {'initial_was': initial, 'total_diff': 0}
                    
                    stats[sku]['total_diff'] += diff
            except:
                continue
        return stats
    except Exception as e:
        print(f"SQL Active SKUs Stats Error: {e}")
        return {}
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
    """Запись в историю с жестким лимитом в 400 строк для поддержания лаконичности БД."""
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