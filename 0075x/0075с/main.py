import threading
from db import *

# Запуск бота
if __name__ == "__main__":
    print(f"[{get_time()}] Бот запускается...")
    try:
        check_db_file()
        init_db()
        backup_thread = threading.Thread(target=auto_backup, daemon=True)
        backup_thread.start()

        while True:
            try:
                bot.polling(none_stop=True)
            except Exception as e:
                print(f"[{get_time()}] Ошибка в основном цикле: {e}")
                log_action(0, f"Ошибка в основном цикле: {str(e)}", is_error=True)
                sleep(10)
    except KeyboardInterrupt:
        print(f"[{get_time()}] Бот остановлен пользователем")
        log_action(0, "Бот остановлен пользователем")
        try:
            backup_db()
        except:
            pass
    except Exception as e:
        print(f"[{get_time()}] Критическая ошибка: {e}")
        try:
            backup_db()
        except:
            pass
        notify_admin(f"Бот остановлен с ошибкой: {str(e)}")
        raise