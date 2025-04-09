from database.db import get_connection
from config import DB_NAME

def log_action(user_id: int, action: str, is_error: bool = False):
    """Логирует действие в БД."""
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO logs (user_id, action, timestamp) VALUES (?, ?, ?)",
            (user_id, f"{'🚨 ' if is_error else ''}{action}", datetime.now())
        )
        conn.commit()