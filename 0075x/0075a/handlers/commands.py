from telebot import TeleBot
from database.models import User
from utils.logger import log_action

def register_handlers(bot: TeleBot):
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        """Обработчик команды /start."""
        User.create(
            message.chat.id,
            message.from_user.username,
            message.from_user.first_name,
            message.from_user.last_name
        )
        log_action(message.chat.id, "Запуск бота")
        bot.reply_to(message, "Добро пожаловать!")