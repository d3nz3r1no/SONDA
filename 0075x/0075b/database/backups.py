from datetime import datetime
from config import DB_NAME
from utils.logger import log_action
from utils.notifier import notify_admin
from database.db import handle_db_errors
from database.decorators import handle_db_errors, admin_required



@handle_db_errors
def backup_db():
    """
    Создает резервную копию базы данных с обработкой ошибок.
    В случае критической ошибки пытается создать аварийную копию.
    """
    try:
        # Создание обычной резервной копии
        backup_name = f"sonda_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        with open(DB_NAME, 'rb') as src, open(backup_name, 'wb') as dst:
            dst.write(src.read())
        log_action(0, f"Создана резервная копия: {backup_name}")

    except Exception as e:
        log_action(0, f"Ошибка резервирования: {str(e)}", is_error=True)

        try:
            # Попытка создать аварийную копию
            emergency_name = f"emergency_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            with open(DB_NAME, 'rb') as src, open(emergency_name, 'wb') as dst:
                dst.write(src.read())
            log_action(0, f"Создана аварийная копия: {emergency_name}")

        except Exception as e2:
            # Критическая ошибка - уведомляем администратора
            error_msg = f"Критическая ошибка резервирования: {str(e2)}"
            log_action(0, error_msg, is_error=True)
            notify_admin(error_msg)


def auto_backup():
    """
    Фоновая задача для автоматического резервного копирования.
    Выполняется с интервалом BACKUP_INTERVAL_DAYS.
    """
    import time
    from config import BACKUP_INTERVAL_DAYS

    while True:
        time.sleep(BACKUP_INTERVAL_DAYS * 86400)  # Конвертация дней в секунды
        backup_db()