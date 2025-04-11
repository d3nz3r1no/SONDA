import logging
import threading
from telebot import TeleBot
from db import Database
from properties import TOKEN, ADMIN_ID
import buttoms_sys
import cmd

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BotApp:
    def __init__(self):
        self.bot = TeleBot(TOKEN)
        self.db = Database()
        self.shutdown_flag = threading.Event()

        # Регистрация обработчиков
        self.register_handlers()

    def register_handlers(self):
        """Регистрация всех обработчиков команд и кнопок"""
        # Команды из cmd.py
        self.bot.message_handler(commands=['start'])(cmd.send_welcome)
        self.bot.message_handler(commands=['help'])(cmd.send_help)
        self.bot.message_handler(commands=['mylogs'])(cmd.show_my_logs)
        self.bot.message_handler(commands=['clearmyhistory'])(cmd.clear_user_history)

        # Обработчики кнопок из buttoms_sys.py
        self.bot.message_handler(content_types=['text'])(buttoms_sys.handle_buttons)

    # main.py (исправленная часть)
    def auto_backup(self):
        """Фоновая задача для автоматического резервного копирования"""
        import time
        while not self.shutdown_flag.is_set():
            try:
                success = self.db.backup_db()
                if success:
                    logger.info("Резервное копирование БД выполнено успешно")
                else:
                    logger.error("Не удалось создать резервную копию БД")

                # Ожидаем 24 часа (86400 секунд) до следующей попытки
                time.sleep(86400)

            except Exception as e:
                logger.error(f"Ошибка в процессе резервного копирования: {str(e)}")
                time.sleep(3600)  # При ошибке ждем 1 час перед повторной попыткой

    def run(self):
        """Основной цикл работы бота"""
        try:
            # Инициализация БД
            if not self.db.init_db():
                logger.critical("Не удалось инициализировать БД")
                return

            # Запуск фоновых задач
            backup_thread = threading.Thread(target=self.auto_backup, daemon=True)
            backup_thread.start()

            logger.info("Бот запущен и готов к работе")
            self.bot.infinity_polling()

        except KeyboardInterrupt:
            logger.info("Бот остановлен пользователем")
        except Exception as e:
            logger.critical(f"Критическая ошибка: {e}")
            self.notify_admin(f"Бот упал с ошибкой: {str(e)}")
        finally:
            self.shutdown()

    def shutdown(self):
        """Корректное завершение работы"""
        self.shutdown_flag.set()
        logger.info("Завершение работы бота...")

    def notify_admin(self, message):
        """Уведомление администратора"""
        try:
            self.bot.send_message(ADMIN_ID, f"🚨 {message}")
        except Exception as e:
            logger.error(f"Не удалось уведомить администратора: {e}")


if __name__ == "__main__":
    app = BotApp()
    app.run()