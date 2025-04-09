import threading
from time import sleep
from telebot import TeleBot
from config import TOKEN
from database.db import init_db, check_db_file
from database.backups import auto_backup
from handlers.commands import register_command_handlers
from handlers.calculator import register_calculator_handlers
from handlers.passwords import register_password_handlers
from handlers.admin import register_admin_handlers
from utils.logger import log_action

def get_time():
    """Возвращает текущее время в формате HH:MM:SS"""
    from datetime import datetime
    return datetime.now().strftime("%H:%M:%S")

def main():
    # Инициализация бота
    bot = TeleBot(TOKEN)
    print(f"[{get_time()}] Бот запускается...")

    # Проверка и инициализация БД
    try:
        check_db_file()
        init_db()
        print(f"[{get_time()}] База данных готова")
    except Exception as e:
        print(f"[{get_time()}] Критическая ошибка БД: {e}")
        log_action(0, f"Ошибка инициализации БД: {str(e)}", is_error=True)
        return

    # Запуск фоновых задач
    backup_thread = threading.Thread(target=auto_backup, daemon=True)
    backup_thread.start()
    print(f"[{get_time()}] Фоновые задачи запущены")

    # Регистрация обработчиков
    register_command_handlers(bot)
    register_calculator_handlers(bot)
    register_password_handlers(bot)
    register_admin_handlers(bot)
    print(f"[{get_time()}] Обработчики зарегистрированы")

    # Основной цикл работы бота
    while True:
        try:
            print(f"[{get_time()}] Запуск бота...")
            bot.polling(none_stop=True, interval=3, timeout=60)
        except Exception as e:
            print(f"[{get_time()}] Ошибка в основном цикле: {e}")
            log_action(0, f"Ошибка в основном цикле: {str(e)}", is_error=True)
            sleep(10)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"[{get_time()}] Бот остановлен пользователем")
        log_action(0, "Бот остановлен пользователем")
    except Exception as e:
        print(f"[{get_time()}] Критическая ошибка: {e}")
        log_action(0, f"Критическая ошибка: {str(e)}", is_error=True)
        raise