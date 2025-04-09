from telebot import TeleBot
from config import ADMIN_ID
from utils.logger import log_action

def register_handlers(bot: TeleBot):
    @bot.message_handler(commands=['logs'], chat_ids=[ADMIN_ID])
    def show_logs(message):
        """Показывает логи (только для админа)."""
        log_action(message.chat.id, "Админ запросил логи")
        bot.reply_to(message, "Вот последние логи...")