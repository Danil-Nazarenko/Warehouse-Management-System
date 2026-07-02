import data_manager
from datetime import datetime

def log_action(action_text, status="Инфо"):
    """
    Отправляет запись о действии в базу данных SQL.
    Больше никаких JSON-файлов!
    """
    try:
        data_manager.add_history_record(
            filename="Действие пользователя", 
            status=status, 
            details={"action": action_text}
        )
    except Exception as e:
        print(f"Ошибка логирования в БД: {e}")