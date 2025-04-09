from db import *
from dberrorslog import *

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