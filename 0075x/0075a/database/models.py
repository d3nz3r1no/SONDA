from database.db import get_connection

class User:
    @staticmethod
    def create(user_id, username, first_name, last_name):
        """Добавляет пользователя в БД."""
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO users VALUES (?, ?, ?, ?, ?)",
                (user_id, username, first_name, last_name, datetime.now())
            )
            conn.commit()