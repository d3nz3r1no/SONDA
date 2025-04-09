import sqlite3
from datetime import datetime
from config import DB_NAME
from utils.logger import log_action
from database.decorators import handle_db_errors, admin_required


def handle_db_errors(func):
    """
    Декоратор для обработки ошибок базы данных
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except sqlite3.OperationalError as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Ошибка базы данных: {e}")
            log_action(args[0].chat.id if args else 0, f"DB Error: {str(e)}", is_error=True)
            return None
        except sqlite3.IntegrityError as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Ошибка целостности данных: {e}")
            log_action(args[0].chat.id if args else 0, f"Integrity Error: {str(e)}", is_error=True)
            return None
        except sqlite3.Error as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Неизвестная ошибка SQLite: {e}")
            log_action(args[0].chat.id if args else 0, f"Unknown SQL Error: {str(e)}", is_error=True)
            return None

    return wrapper


def get_connection():
    """
    Возвращает подключение к базе данных с настроенным режимом WAL
    """
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


@handle_db_errors
def init_db():
    """
    Инициализирует базу данных и создает необходимые таблицы
    """
    try:
        with get_connection() as conn:
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
            cursor.executescript('''
            CREATE INDEX IF NOT EXISTS idx_logs_user ON logs(user_id);
            CREATE INDEX IF NOT EXISTS idx_calc_user ON calculations(user_id);
            CREATE INDEX IF NOT EXISTS idx_logs_time ON logs(timestamp);
            ''')

            # Очистка старых данных
            cursor.execute("DELETE FROM logs WHERE timestamp < datetime('now', '-30 days')")

            print(f"[{datetime.now().strftime('%H:%M:%S')}] Инициализация БД завершена")
            conn.commit()

    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Критическая ошибка инициализации БД: {e}")
        raise


def check_db_file():
    """
    Проверяет существование файла БД и инициализирует новую БД при необходимости
    """
    try:
        if not os.path.exists(DB_NAME):
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Файл БД не найден, будет создан новый")
            init_db()
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Файл БД найден")
        return True
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Ошибка проверки файла БД: {e}")
        raise