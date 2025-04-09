from log_action import *
import sqlite3
from notifyadmin import *
from datetime import datetime
from time import sleep
import os

def handle_db_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except sqlite3.OperationalError as e:
            error_msg = f"Ошибка БД: {e}"
            print(f"[{get_time()}] {error_msg}")
            log_action(0, error_msg, is_error=True)
            return None
        except Exception as e:
            error_msg = f"Неизвестная ошибка: {e}"
            print(f"[{get_time()}] {error_msg}")
            log_action(0, error_msg, is_error=True)
            return None
    return wrapper

@handle_db_errors
def init_db():
    """Инициализирует базу данных и создает необходимые таблицы"""
    try:
        with sqlite3.connect('sonda_bot.db') as conn:
            cursor = conn.cursor()

            # Основные таблицы
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

            # Очистка старых данных
            cursor.execute("DELETE FROM logs WHERE timestamp < datetime('now', '-30 days')")

            print(f"[{get_time()}] Инициализация БД завершена")
            conn.commit()

        backup_db()
    except Exception as e:
        print(f"[{get_time()}] Критическая ошибка инициализации БД: {e}")
        raise

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
    """Проверяет и создает файл БД при необходимости"""
    try:
        db_dir = os.path.dirname(os.path.abspath('sonda_bot.db'))
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)

        if not os.path.exists('sonda_bot.db'):
            print(f"[{get_time()}] Файл БД не найден, создаю новый...")
            init_db()  # Создаст файл и таблицы
        else:
            print(f"[{get_time()}] Файл БД найден")
    except Exception as e:
        print(f"[{get_time()}] Критическая ошибка при проверке БД: {e}")
        raise