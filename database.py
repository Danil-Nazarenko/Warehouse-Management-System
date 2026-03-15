import sqlite3
import os

DB_NAME = 'ordo_v2.db'

def get_connection():
    """Создает подключение с оптимизацией WAL для слабого ПК."""
    conn = sqlite3.connect(DB_NAME)
    # Режим WAL позволяет читать и писать одновременно без тормозов
    conn.execute('PRAGMA journal_mode = WAL;')
    # Синхронизация NORMAL ускоряет запись, не рискуя целостностью данных
    conn.execute('PRAGMA synchronous = NORMAL;')
    return conn

def init_db():
    """Инициализация структуры таблиц и индексов."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Склад
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            sku TEXT PRIMARY KEY,
            quantity INTEGER DEFAULT 0
        )
    ''')
    # Индекс для быстрого поиска по артикулу
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_inv_sku ON inventory(sku)')

    # 2. Рецепты
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            sku TEXT PRIMARY KEY,
            content TEXT
        )
    ''')

    # 3. Последние товары
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recent_items (
            sku TEXT PRIMARY KEY,
            last_used TIMESTAMP
        )
    ''')
    # Индекс для быстрой сортировки списка "Актуальное"
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_recent_used ON recent_items(last_used)')

    # 4. История
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            filename TEXT,
            status TEXT,
            details TEXT
        )
    ''')

    conn.commit()
    conn.close()
    # Печатаем только один раз при старте
    # print("🚀 База Ordo v2.1.0 готова (режим WAL)")

if __name__ == "__main__":
    init_db()