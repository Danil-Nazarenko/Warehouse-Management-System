import json
import os
from datetime import datetime
import sys

def get_base_path():
    # Если запущено как скомпилированный EXE
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    
    # Если запущен обычный .py скрипт
    # Находим папку, где лежит этот файл (сейчас это /gui)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Если мы находимся внутри папки 'gui', поднимаемся на уровень выше в корень
    if os.path.basename(current_dir) == 'gui':
        return os.path.dirname(current_dir)
    
    return current_dir

# Теперь HISTORY_FILE всегда будет указывать на корень проекта
HISTORY_FILE = os.path.join(get_base_path(), 'history.json')

def log_action(action_text):
    """Добавляет запись в историю с текущим временем."""
    # Оставим формат с датой для точности, но выводить в интерфейс можем только время
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    new_entry = {
        "time": timestamp,
        "action": action_text
    }

    history = []
    # Проверяем наличие файла перед чтением
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except Exception:
            # Если файл поврежден, начинаем с чистого листа
            history = []

    # Добавляем новую запись в самое начало списка
    history.insert(0, new_entry)
    
    # Храним только последние 500 событий, чтобы файл не рос бесконечно
    history = history[:500]

    # Сохраняем обратно в файл
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Ошибка записи истории: {e}")