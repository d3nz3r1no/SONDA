import threading
from datetime import datetime
from db import check_db_file, init_db, auto_backup
from cmd import bot
from buttoms_sys import handle_buttons
from log_action import log_action
from notifyadmin import notify_admin


def get_time():
    """Функция для получения текущего времени"""
    return datetime.now().strftime("%H:%M:%S")


def main():
    """Основная функция запуска бота"""
    print(f"[{get_time()}] Бот запускается...")

    try:
        # Инициализация базы данных
        check_db_file()
        init_db()

        # Запуск фонового копирования
        backup_thread = threading.Thread(target=auto_backup, daemon=True)
        backup_thread.start()

        # Явная регистрация обработчика кнопок
        bot.message_handler(content_types=['text'])(handle_buttons)

        # Запуск бота (TOKEN используется внутри объекта bot из cmd.py)
        bot.polling(none_stop=True, interval=1, timeout=30)

    except KeyboardInterrupt:
        print(f"[{get_time()}] Бот остановлен пользователем")
        log_action(0, "Бот остановлен пользователем")
    except Exception as e:
        error_msg = f"Критическая ошибка: {e}"
        print(f"[{get_time()}] {error_msg}")
        log_action(0, error_msg, is_error=True)
        notify_admin(error_msg)


if __name__ == "__main__":
    main()