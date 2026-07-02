import sqlite3
import os

DB_NAME = 'ordo_v2.db'

def get_connection():
    """Создает подключение с оптимизацией WAL для слабого ПК."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute('PRAGMA journal_mode = WAL;')
    conn.execute('PRAGMA synchronous = NORMAL;')
    return conn

def init_db():
    """Инициализация структуры таблиц и индексов."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            sku TEXT PRIMARY KEY,
            quantity INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_inv_sku ON inventory(sku)')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            sku TEXT PRIMARY KEY,
            content TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recent_items (
            sku TEXT PRIMARY KEY,
            last_used TIMESTAMP
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_recent_used ON recent_items(last_used)')

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

if __name__ == "__main__":
    init_db()