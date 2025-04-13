import logging
from datetime import datetime
from cmd import bot, log_action
from buttoms import markup, hellokeys, menubot
from calc_sys import *

# Настройка логгера
logger = logging.getLogger(__name__)

def get_time():
    """Возвращает форматированное текущее время"""
    return datetime.now().strftime("%H:%M:%S")

@bot.message_handler(content_types=['text'])
def handle_buttons(message):
    """Основной обработчик текстовых сообщений (кнопок)"""
    try:
        if message.text == "👋 Привет":
            handle_greeting(message)
        elif message.text == "❓ Помощь":
            handle_help(message)
        elif message.text == "Обо мне ❓":
            handle_about(message)
        elif message.text == "⚙️ Меню":
            handle_menu(message)
        elif message.text == "➗ Калькулятор":
            handle_calculator_start(message)
        elif message.text == "🔒 Пароли":
            print("Нажато")
        elif message.chat.id in user_calculations:
            handle_calculator_input(message)
    except Exception as e:
        error_msg = f"Ошибка обработки кнопки: {str(e)}"
        logger.error(error_msg)
        bot.reply_to(message, "⚠ Произошла ошибка. Попробуйте еще раз.")
        log_action(message.chat.id, error_msg, is_error=True)


def handle_greeting(message):
    """Обработчик кнопки приветствия"""
    bot.reply_to(message,
                 "Привет. Я - Твой мощный инструмент\nГруппа тестировщиков - https://t.me/sondatest\nКанал про меня - https://t.me/sondachanel",
                 reply_markup=hellokeys)
    log_action(message.chat.id, "Нажата кнопка Привет")

def handle_help(message):
    """Обработчик кнопки помощи"""
    help_text = (
        "Команды бота:\n\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать это сообщение\n"
        "/mylogs - Ваши последние действия\n"
        "/history - История ваших вычислений\n"
        "/clearmyhistory - Очистить вашу историю\n\n"
        "Бот разрабатывается с целью быть полезным. Для этого есть пока что только калькулятор.\n"
    )
    bot.reply_to(message, help_text)
    log_action(message.chat.id, "Запрошена помощь")


def handle_about(message):
    """Обработчик кнопки 'Обо мне'"""
    about_text = (
        "Обо мне:\n\n"
        "Я - SONDA, создана для удобства человека.\n"
        "Группа тестировщиков - https://t.me/sondatest\n"
        "Канал про меня - https://t.me/sondachanel\n\n"
        "Версия: 0.0.81"
    )
    bot.reply_to(message, about_text, reply_markup=markup)
    log_action(message.chat.id, "Просмотр информации о боте")

def handle_menu(message):
    """Обработчик кнопки меню"""
    bot.reply_to(message, "Главное меню:", reply_markup=menubot)
    log_action(message.chat.id, "Открыто главное меню")

def handle_calculator_input(message):
    """Обработчик ввода в калькуляторе"""
    try:
        if message.text == "🔙 В меню":
            handle_calculator_exit(message)
        elif message.text == "История 📜":
            show_history(message)
        elif message.text == "Стереть":
            handle_calculator_clear(message)
        elif message.text == "Повторить ♻":
            handle_calculator_repeat(message)
        elif message.text == "res":
            handle_calculator_result(message)
        elif message.text in ["+", "-", "*", "/"]:
            handle_calculator_operator(message)
        elif message.text.isdigit() or message.text == ".":
            handle_calculator_digit(message)
        elif message.text in ["^", "!", "%"]:
            handle_calculator_special(message)
        elif message.text == "√(":
            handle_calculator_sqrt(message)
    except Exception as e:
        error_msg = f"Ошибка в калькуляторе: {str(e)}"
        logger.error(error_msg)
        bot.reply_to(message, "⚠ Ошибка в вычислении. Попробуйте еще раз.")
        log_action(message.chat.id, error_msg, is_error=True)