from datetime import datetime
from config import DB_NAME
from utils.logger import log_action
from utils.notifier import notify_admin
from database.db import handle_db_errors

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
    """Фоновая задача для автоматического бэкапа."""
    import time
    from config import BACKUP_INTERVAL_DAYS

    while True:
        time.sleep(BACKUP_INTERVAL_DAYS * 86400)
        backup_db()