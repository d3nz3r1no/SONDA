from log_action import *

def handle_db_errors(func):
    """Декоратор для обработки ошибок базы данных"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except sqlite3.OperationalError as e:
            print(f"[{get_time()}] Ошибка базы данных: {e}")
            log_action(args[0].chat.id if args else 0, f"DB Error: {str(e)}", is_error=True)
            return None
        except sqlite3.IntegrityError as e:
            print(f"[{get_time()}] Ошибка целостности данных: {e}")
            log_action(args[0].chat.id if args else 0, f"Integrity Error: {str(e)}", is_error=True)
            return None
        except sqlite3.Error as e:
            print(f"[{get_time()}] Неизвестная ошибка SQLite: {e}")
            log_action(args[0].chat.id if args else 0, f"Unknown SQL Error: {str(e)}", is_error=True)
            return None
    return wrapper