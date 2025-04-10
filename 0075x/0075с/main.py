import logging
import threading
from time import sleep
from telebot import TeleBot
from db import Database
from properties import TOKEN, ADMIN_ID
import cmd
import buttoms_sys

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

    def auto_backup(self):
        """Фоновая задача для резервного копирования БД"""
        while not self.shutdown_flag.is_set():
            try:
                if self.db.backup_db():
                    logger.info("Резервная копия БД создана успешно")
                sleep(86400)  # Каждые 24 часа
            except Exception as e:
                logger.error(f"Ошибка при создании резервной копии: {e}")
                sleep(3600)  # Повторить через час при ошибке

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