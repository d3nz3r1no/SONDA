import threading
from db import check_db_file, auto_backup
from cmd import bot
from buttoms_sys import handle_buttons


def main():
    print("[*] Бот запускается...")

    if not check_db_file():
        print("[!] Не удалось инициализировать БД. Работа невозможна.")
        return

    try:
        bot.message_handler(content_types=['text'])(handle_buttons)
        backup_thread = threading.Thread(target=auto_backup, daemon=True)
        backup_thread.start()
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"[!] Критическая ошибка: {e}")


if __name__ == "__main__":
    main()