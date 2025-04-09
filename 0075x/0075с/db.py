from db_init import *
from notifyadmin import *
from time import sleep
import os
from dberrorslog import *

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