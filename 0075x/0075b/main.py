import threading
from time import sleep
from config import TOKEN
from database.db import init_db, check_db_file
from database.backups import auto_backup
from handlers.passwords import register_password_handlers
from utils.logger import log_action
from handlers.commands import *
from handlers.calculator import *
from handlers.admin import *

import logging
logging.basicConfig(level=logging.INFO)

def main():
    try:
        # 1. Инициализация бота
        bot = TeleBot(TOKEN)
        print("[!] Инициализация SONDA bot v0.0.75b")

        # 2. Проверка и инициализация БД
        check_db_file()
        init_db()
        print("[!] База данных готова")

        # 3. Запуск фоновых задач
        backup_thread = threading.Thread(target=auto_backup, daemon=True)
        backup_thread.start()
        print("[!] Фоновые задачи запущены")

        # 4. Регистрация обработчиков
        register_command_handlers(bot)
        register_calculator_handlers(bot)
        register_password_handlers(bot)
        register_admin_handlers(bot)
        print("[!] Обработчики зарегистрированы")

        # 5. Основной цикл
        while True:
            try:
                print("[!] Запуск бота...")
                bot.polling(none_stop=True, interval=3, timeout=30)
            except Exception as e:
                print(f"[ERROR] Ошибка polling: {str(e)}")
                log_action(0, f"Ошибка polling: {str(e)}", is_error=True)
                sleep(10)

    except Exception as e:
        print(f"[CRITICAL] Критическая ошибка: {str(e)}")
        log_action(0, f"Критическая ошибка: {str(e)}", is_error=True)
        raise

if __name__ == "__main__":
    main()