from db import *
from log_action import *
from notifyadmin import *
from time import sleep
import os

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

init_db()

@handle_db_errors
def backup_db():
    """Создает резервную копию базы данных"""
    try:
        backup_name = f"sonda_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        with open('sonda_bot.db', 'rb') as src, open(backup_name, 'wb') as dst:
            dst.write(src.read())
        log_action(0, f"Создана резервная копия: {backup_name}")
    except Exception as e:
        log_action(0, f"Ошибка резервирования: {str(e)}", is_error=True)
        try:
            backup_name = f"emergency_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            with open('sonda_bot.db', 'rb') as src, open(backup_name, 'wb') as dst:
                dst.write(src.read())
            log_action(0, f"Создана аварийная резервная копия: {backup_name}")
        except Exception as e2:
            log_action(0, f"Критическая ошибка резервирования: {str(e2)}", is_error=True)
            notify_admin(f"Не удалось создать резервную копию: {str(e2)}")

def auto_backup():
    """Фоновая задача для автоматического резервного копирования"""
    while True:
        sleep(BACKUP_INTERVAL_DAYS * 86400)  # Конвертация дней в секунды
        backup_db()

def check_db_file():
    """Проверяет существование файла БД"""
    try:
        if not os.path.exists('sonda_bot.db'):
            print(f"[{get_time()}] Файл БД не найден, будет создан новый")
            init_db()
        else:
            print(f"[{get_time()}] Файл БД найден")
        return True
    except Exception as e:
        print(f"[{get_time()}] Ошибка проверки файла БД: {e}")
        raise