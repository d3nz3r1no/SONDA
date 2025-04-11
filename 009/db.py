import os
import time
import sqlite3
from sqlite3 import Error
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
        self.db_path = "data/sonda_bot.db"
        self.timeout = 30  # Увеличиваем таймаут ожидания
        self.max_retries = 3  # Максимальное количество попыток

    def backup_db(self):
        """Создает резервную копию базы данных"""
        try:
            import shutil
            import os
            from datetime import datetime

            # Создаем директорию backups, если её нет
            os.makedirs('backups', exist_ok=True)

            # Формируем имя файла с timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"backups/sonda_backup_{timestamp}.db"

            # Копируем файл БД
            shutil.copy2(self.db_path, backup_path)

            # Проверяем, что копия создана
            if os.path.exists(backup_path):
                return True
            return False

        except Exception as e:
            print(f"Ошибка при создании резервной копии: {e}")
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

    def get_connection(self):
        """Возвращает соединение с БД с повторными попытками"""
        for attempt in range(self.max_retries):
            try:
                conn = sqlite3.connect(
                    self.db_path,
                    timeout=self.timeout,
                    check_same_thread=False  # Разрешаем использование из разных потоков
                )
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA journal_mode=WAL")  # Включаем WAL режим
                return conn
            except Error as e:
                if attempt == self.max_retries - 1:
                    print(f"[{datetime.now()}] Ошибка подключения к БД после {self.max_retries} попыток: {e}")
                    return None
                time.sleep(1)  # Ждем перед повторной попыткой

    def get_db_path(self):
        """Возвращает абсолютный путь к файлу БД"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_dir, "data", "sonda_bot.db")

    def ensure_db_directory(self):
        """Гарантирует существование директории для БД"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)

    # db.py (дополняем метод init_db)
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

                CREATE TABLE IF NOT EXISTS passwords (
                    pass_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    service TEXT NOT NULL,
                    password TEXT NOT NULL,
                    timestamp TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                );
            ''')
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Ошибка инициализации БД: {e}")
            return False

# Глобальный экземпляр БД
db = Database()