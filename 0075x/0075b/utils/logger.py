import sqlite3
from datetime import datetime
from config import DB_NAME
from database.decorators import handle_db_errors
from database.decorators import handle_db_errors, admin_required

@handle_db_errors
def log_action(user_id: int, action: str, is_error: bool = False):
    """
    Логирует действие в базу данных
    Полная реализация из оригинального кода SONDA 0.0.74

    :param user_id: ID пользователя
    :param action: Описание действия
    :param is_error: Флаг ошибки (добавляет 🚨 к записи)
    """
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO logs (user_id, action, timestamp)
                VALUES (?, ?, ?)
            ''', (
                user_id,
                f"{'🚨 ' if is_error else ''}{action}",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()

    except sqlite3.Error as e:
        # Резервное логирование в консоль при ошибках БД
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Ошибка логирования: {e}")
        print(f"Действие: {action}, UserID: {user_id}, Ошибка: {is_error}")


@handle_db_errors
def get_user_logs(user_id: int, limit: int = 10):
    """
    Возвращает логи пользователя
    Реализация из оригинального кода 0.0.74

    :param user_id: ID пользователя
    :param limit: Количество записей
    :return: Список записей лога
    """
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT action, timestamp 
            FROM logs 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (user_id, limit))
        return cursor.fetchall()


@handle_db_errors
def get_system_logs(limit: int = 20):
    """
    Возвращает системные логи (для администратора)
    Реализация из оригинального кода 0.0.74

    :param limit: Количество записей
    :return: Список системных логов
    """
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id, action, timestamp 
            FROM logs 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()


@handle_db_errors
def cleanup_logs(days: int = 30):
    """
    Очищает старые логи (старше указанного количества дней)
    Реализация из оригинального кода 0.0.74

    :param days: Количество дней для хранения логов
    """
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM logs WHERE timestamp < datetime('now', ?)",
            (f'-{days} days',)
        )
        conn.commit()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Очищены логи старше {days} дней")