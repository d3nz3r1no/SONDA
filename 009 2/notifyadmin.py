from properties import *
from gettime import *

def notify_admin(error_msg):
    """Отправляет уведомление администратору об ошибке"""
    try:
        bot.send_message(ADMIN_ID, f"🚨 Критическая ошибка:\n{error_msg}")
    except Exception as e:
        print(f"[{get_time()}] Не удалось уведомить администратора: {e}")

def is_admin(user_id):
    """Проверяет, является ли пользователь администратором"""
    return user_id == ADMIN_ID