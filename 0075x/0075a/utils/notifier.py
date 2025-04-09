from telebot import TeleBot
from config import TOKEN, ADMIN_ID

bot = TeleBot(TOKEN)

def notify_admin(error_msg: str):
    try:
        bot.send_message(ADMIN_ID, f"🚨 Ошибка: {error_msg}")
    except Exception as e:
        from utils.logger import log_action
        log_action(0, f"Ошибка уведомления админа: {e}", is_error=True)