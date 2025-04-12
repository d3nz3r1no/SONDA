import os
import sqlite3
from datetime import datetime

def handle_db_errors(func):
    """Декоратор для обработки ошибок БД"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except sqlite3.Error as e:
            print(f"[Ошибка БД] {e}")
            return None
    return wrapper

class Database:
    def __init__(self):
        self.db_path = self.get_db_path()
        self.backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")
        self.ensure_db_directory()

    def backup_db(self):
        """
        Создает резервную копию базы данных с проверкой ошибок и логированием
        Возвращает True при успешном копировании, False при ошибке
        """
        try:
            import shutil
            import os

            # Пути к файлам
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sonda_bot.db")
            backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")

            # Создаем директорию для бэкапов, если не существует
            os.makedirs(backup_dir, exist_ok=True)

            # Формируем имя файла с timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"sonda_backup_{timestamp}.db")

            # Проверяем существование основного файла БД
            if not os.path.exists(db_path):
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Файл БД не найден для резервного копирования")
                return False

            # Создаем резервную копию
            shutil.copy2(db_path, backup_path)

            # Проверяем, что копия создана
            if not os.path.exists(backup_path):
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Ошибка: резервная копия не создана")
                return False

            print(f"[{datetime.now().strftime('%H:%M:%S')}] Резервная копия создана: {backup_path}")

            # Удаляем старые бэкапы (оставляем последние 5)
            backups = sorted([f for f in os.listdir(backup_dir) if f.startswith("sonda_backup_")])
            for old_backup in backups[:-5]:
                os.remove(os.path.join(backup_dir, old_backup))

            return True

        except PermissionError as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Ошибка прав доступа при резервном копировании: {e}")
            return False
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Критическая ошибка при резервном копировании: {e}")
            return False

    def get_db_path(self):
        """Возвращает абсолютный путь к файлу БД"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_dir, "data", "sonda_bot.db")

    def ensure_db_directory(self):
        """Гарантирует существование директории для БД"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)

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
                CREATE TABLE IF NOT EXISTS master_keys (
                    user_id INTEGER PRIMARY KEY,
                    master_key_hash TEXT NOT NULL
                );
            
                CREATE TABLE IF NOT EXISTS passwords (
                    pass_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    service_name TEXT NOT NULL,
                    encrypted_password TEXT NOT NULL,
                    iv TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
            ''')
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Ошибка инициализации БД: {e}")
            return False

# Глобальный экземпляр БД
db = Database()