from telebot import types

def get_main_menu():
    """Возвращает клавиатуру главного меню."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("👋 Привет", "❓ Помощь", "➗ Калькулятор")
    return markup