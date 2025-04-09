import sqlite3
from functools import wraps
from datetime import datetime
from config import DB_NAME
from utils.logger import log_action
from database.decorators import handle_db_errors, admin_required


def handle_db_errors(func):
    """
    Декоратор для обработки ошибок базы данных
    Оригинальная реализация из SONDA 0.0.74
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except sqlite3.OperationalError as e:
            error_msg = f"Ошибка базы данных: {str(e)}"
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {error_msg}")
            log_action(args[0].chat.id if args and hasattr(args[0], 'chat') else 0,
                       f"DB Error: {str(e)}",
                       is_error=True)
            return None
        except sqlite3.IntegrityError as e:
            error_msg = f"Ошибка целостности данных: {str(e)}"
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {error_msg}")
            log_action(args[0].chat.id if args and hasattr(args[0], 'chat') else 0,
                       f"Integrity Error: {str(e)}",
                       is_error=True)
            return None
        except sqlite3.Error as e:
            error_msg = f"Неизвестная ошибка SQLite: {str(e)}"
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {error_msg}")
            log_action(args[0].chat.id if args and hasattr(args[0], 'chat') else 0,
                       f"Unknown SQL Error: {str(e)}",
                       is_error=True)
            return None

    return wrapper


def admin_required(func):
    """
    Декоратор для проверки прав администратора
    (Реализация из оригинального кода 0.0.74)
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        message = args[0]
        from config import ADMIN_ID
        if message.chat.id != ADMIN_ID:
            bot.reply_to(message, "⛔ Доступ запрещен")
            log_action(message.chat.id, "Попытка доступа к админ-функции", is_error=True)
            return
        return func(*args, **kwargs)

    return wrapper


def log_actions(func):
    """
    Декоратор для логирования действий пользователей
    (Использовался в оригинальной версии 0.0.74)
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        message = args[0]
        action_name = func.__name__

        try:
            result = func(*args, **kwargs)
            log_action(message.chat.id, f"Выполнено: {action_name}")
            return result
        except Exception as e:
            log_action(message.chat.id, f"Ошибка в {action_name}: {str(e)}", is_error=True)
            raise

    return wrapper


def validate_input(pattern: str = None):
    """
    Декоратор для валидации ввода пользователя
    (Аналог проверок из оригинального калькулятора)
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            message = args[0]
            if pattern and not re.match(pattern, message.text):
                bot.reply_to(message, "⚠ Некорректный ввод")
                log_action(message.chat.id, f"Невалидный ввод в {func.__name__}", is_error=True)
                return
            return func(*args, **kwargs)

        return wrapper

    return decorator