from gettime import *
import sqlite3

def log_action(user_id, action, is_error=False):
    """Логирует действие в базу данных"""
    try:
        with sqlite3.connect('sonda_bot.db') as conn:
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
        print(f"[{get_time()}] Ошибка логирования: {e}")