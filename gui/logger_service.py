import data_manager
from datetime import datetime

def log_action(action_text, status="Инфо"):
    """
    Отправляет запись о действии в базу данных SQL.
    Больше никаких JSON-файлов!
    """
    try:
        # Теперь мы просто вызываем наш универсальный метод из data_manager
        # Он сам знает, как подключиться к БД и сделать запись
        data_manager.add_history_record(
            filename="Действие пользователя", 
            status=status, 
            details={"action": action_text}
        )
    except Exception as e:
        # Если база вдруг занята, просто выведем в консоль, чтобы не вешать приложение
        print(f"Ошибка логирования в БД: {e}")