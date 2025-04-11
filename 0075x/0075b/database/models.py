import sqlite3
from datetime import datetime
from database.db import get_connection, handle_db_errors
from database.decorators import handle_db_errors, admin_required

class User:
    @staticmethod
    @handle_db_errors
    def create(user_id: int, username: str, first_name: str, last_name: str):
        """Создает нового пользователя в базе данных"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO users 
                (user_id, username, first_name, last_name, registration_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                user_id,
                username,
                first_name,
                last_name,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()

    @staticmethod
    @handle_db_errors
    def exists(user_id: int) -> bool:
        """Проверяет существование пользователя"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
            return cursor.fetchone() is not None

class Log:
    @staticmethod
    @handle_db_errors
    def add(user_id: int, action: str, is_error: bool = False):
        """Добавляет запись в лог"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO logs 
                (user_id, action, timestamp)
                VALUES (?, ?, ?)
            ''', (
                user_id,
                f"{'🚨 ' if is_error else ''}{action}",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()

    @staticmethod
    @handle_db_errors
    def get_user_logs(user_id: int, limit: int = 10):
        """Возвращает логи пользователя"""
        with get_connection() as conn:
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

    @staticmethod
    @handle_db_errors
    def get_all_logs(limit: int = 10):
        with get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM logs 
                ORDER BY log_id DESC 
                LIMIT ?
            ''', (limit,))
            return cursor.fetchall()

class Calculation:
    @staticmethod
    @handle_db_errors
    def add(user_id: int, expression: str, result: str):
        """Добавляет вычисление в историю"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO calculations 
                (user_id, expression, result, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (
                user_id,
                expression,
                result,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()

    @staticmethod
    @handle_db_errors
    def get_last(user_id: int):
        """Возвращает последнее вычисление пользователя"""
        with get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT expression, result 
                FROM calculations 
                WHERE user_id = ? 
                ORDER BY calc_id DESC 
                LIMIT 1
            ''', (user_id,))
            return cursor.fetchone()

    @staticmethod
    @handle_db_errors
    def get_history(user_id: int, limit: int = 5):
        """Возвращает историю вычислений"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT expression, result, timestamp 
                FROM calculations 
                WHERE user_id = ? 
                ORDER BY calc_id DESC 
                LIMIT ?
            ''', (user_id, limit))
            return cursor.fetchall()

    @staticmethod
    @handle_db_errors
    def clear_history(user_id: int):
        """Очищает историю вычислений пользователя"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM calculations WHERE user_id = ?', (user_id,))
            conn.commit()

class Password:
    @staticmethod
    def add(user_id, service, login, password, notes=""):
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO passwords VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, service, login, password, notes, datetime.now())
            )
            conn.commit()

    @staticmethod
    def get_all(user_id):
        with get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM passwords WHERE user_id = ?", (user_id,))
            return cursor.fetchall()