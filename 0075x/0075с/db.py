import os
import sqlite3
from datetime import datetime
from log_action import log_action
from time import sleep
from properties import BACKUP_INTERVAL_DAYS


def get_db_path():
    """Возвращает абсолютный путь к файлу БД"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "sonda_bot.db")


def handle_db_errors(func):
    """Декоратор для обработки ошибок БД"""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except sqlite3.Error as e:
            error_msg = f"Ошибка БД: {e}"
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {error_msg}")
            log_action(0, error_msg, is_error=True)
            return None
    return wrapper

@handle_db_errors
def init_db():
    """Инициализация БД с гарантированным созданием директории"""
    db_path = get_db_path()
    db_dir = os.path.dirname(db_path)

    # Создаем директорию, если не существует
    os.makedirs(db_dir, exist_ok=True)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Создаем таблицы
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

        # Оптимизации
        cursor.execute('PRAGMA journal_mode=WAL')
        cursor.executescript('''
        CREATE INDEX IF NOT EXISTS idx_logs_user ON logs(user_id);
        CREATE INDEX IF NOT EXISTS idx_calc_user ON calculations(user_id);
        CREATE INDEX IF NOT EXISTS idx_logs_time ON logs(timestamp);
        ''')
        conn.commit()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] БД успешно инициализирована")
        return True
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Критическая ошибка: {e}")
        return False

def backup_db():
    """Создает резервную копию БД с проверкой пути"""
    try:
        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = os.path.join(backup_dir, f"sonda_backup_{timestamp}.db")

        with open('sonda_bot.db', 'rb') as src, open(backup_name, 'wb') as dst:
            dst.write(src.read())

        log_action(0, f"Резервная копия создана: {backup_name}")
    except Exception as e:
        log_action(0, f"Ошибка резервирования: {e}", is_error=True)

def auto_backup():
    """Фоновая задача для автоматического резервного копирования"""
    while True:
        sleep(BACKUP_INTERVAL_DAYS * 86400)  # Конвертация дней в секунды
        backup_db()

def check_db_file():
    """Проверка и создание БД с обработкой ошибок"""
    db_path = get_db_path()
    if not os.path.exists(db_path):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Файл БД не найден, создаю новый...")
        return init_db()
    return True