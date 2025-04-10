import os
import sqlite3
from datetime import datetime


class Database:
    def __init__(self):
        self.db_path = self.get_db_path()
        self.ensure_db_directory()

    def get_db_path(self):
        """Возвращает абсолютный путь к файлу БД"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_dir, "data", "sonda_bot.db")

    def ensure_db_directory(self):
        """Гарантирует существование директории для БД"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def get_connection(self):
        """Возвращает соединение с БД с обработкой ошибок"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Ошибка подключения к БД: {e}")
            return None

    def init_db(self):
        """Инициализация таблиц в БД"""
        conn = self.get_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.executescript('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    registration_date TEXT
                );

                CREATE TABLE IF NOT EXISTS logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT,
                    timestamp TEXT
                );

                CREATE TABLE IF NOT EXISTS calculations (
                    calc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    expression TEXT,
                    result TEXT,
                    timestamp TEXT
                );
            ''')
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Ошибка инициализации БД: {e}")
            return False
        finally:
            conn.close()


# Глобальный экземпляр БД
db = Database()