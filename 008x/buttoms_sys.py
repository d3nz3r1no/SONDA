import logging
from datetime import datetime
from db import db
from cmd import bot, log_action
from buttoms import markup, hellokeys, menubot, calcmarkup
from calc_sys import safe_calc
import sqlite3

# Настройка логгера
logger = logging.getLogger(__name__)

# Глобальный словарь для хранения текущих вычислений
user_calculations = {}


def get_time():
    """Возвращает форматированное текущее время"""
    return datetime.now().strftime("%H:%M:%S")


def save_calculation(user_id, expression, result):
    """Сохраняет вычисление в БД"""
    try:
        conn = db.get_connection()
        if not conn:
            logger.error("Не удалось подключиться к БД для сохранения вычисления")
            return False

        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO calculations (user_id, expression, result, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (
            user_id,
            expression,
            result,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения вычисления: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()


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


def handle_calculator_start(message):
    """Обработчик запуска калькулятора"""
    user_calculations[message.chat.id] = ""
    bot.send_message(message.chat.id,
                     "Режим калькулятора. Вводите выражение:",
                     reply_markup=calcmarkup)
    log_action(message.chat.id, "Запущен калькулятор")


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


def handle_calculator_exit(message):
    """Выход из калькулятора"""
    if message.chat.id in user_calculations:
        del user_calculations[message.chat.id]
    bot.send_message(message.chat.id, "Возврат в меню:", reply_markup=markup)
    log_action(message.chat.id, "Выход из калькулятора")


def show_history(message):
    """Показывает историю вычислений"""
    try:
        conn = db.get_connection()
        if not conn:
            bot.reply_to(message, "⏳ Сервис временно недоступен.")
            return

        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT expression, result, timestamp 
            FROM calculations 
            WHERE user_id = ? 
            ORDER BY calc_id DESC 
            LIMIT 5
        ''', (message.chat.id,))

        history = cursor.fetchall()

        if not history:
            bot.send_message(message.chat.id,
                             "История вычислений пуста",
                             reply_markup=calcmarkup)
            return

        response = "📝 Ваши последние вычисления:\n\n"
        for item in history:
            response += f"▸ {item['expression']} = {item['result']}\n"
            response += f"⏱ {item['timestamp']}\n\n"

        bot.send_message(message.chat.id, response, reply_markup=calcmarkup)
        log_action(message.chat.id, "Просмотр истории в калькуляторе")
    finally:
        if conn:
            conn.close()


def handle_calculator_clear(message):
    """Очистка текущего выражения"""
    user_calculations[message.chat.id] = ""
    bot.send_message(message.chat.id,
                     "Калькулятор очищен. Текущее: 0",
                     reply_markup=calcmarkup)
    log_action(message.chat.id, "Очистка калькулятора")


def handle_calculator_repeat(message):
    """Повтор последнего вычисления"""
    try:
        conn = db.get_connection()
        if not conn:
            bot.send_message(message.chat.id,
                             "⏳ Сервис временно недоступен.",
                             reply_markup=calcmarkup)
            return

        cursor = conn.cursor()
        cursor.execute('''
            SELECT expression 
            FROM calculations 
            WHERE user_id = ? 
            ORDER BY calc_id DESC 
            LIMIT 1
        ''', (message.chat.id,))

        last_calc = cursor.fetchone()

        if last_calc:
            user_calculations[message.chat.id] = last_calc[0]
            bot.send_message(message.chat.id,
                             f"↩ Повтор: {last_calc[0]}",
                             reply_markup=calcmarkup)
        else:
            bot.send_message(message.chat.id,
                             "Нет истории вычислений",
                             reply_markup=calcmarkup)
    finally:
        if conn:
            conn.close()


def handle_calculator_result(message):
    """Вычисление результата"""
    if not user_calculations.get(message.chat.id):
        bot.send_message(message.chat.id,
                         "Введите выражение сначала",
                         reply_markup=calcmarkup)
        return

    expression = user_calculations[message.chat.id].strip()

    # Автодобавление закрывающей скобки для корня
    if '√(' in expression and expression.count('(') > expression.count(')'):
        expression += ")"
        user_calculations[message.chat.id] = expression

    result = safe_calc(expression)

    if not result.startswith("Ошибка"):
        if save_calculation(message.chat.id, expression, result):
            log_action(message.chat.id, f"Вычисление: {expression} = {result}")

    bot.send_message(message.chat.id,
                     f"Результат: {result}",
                     reply_markup=calcmarkup)


def handle_calculator_operator(message):
    """Добавление оператора"""
    user_calculations[message.chat.id] += f" {message.text} "
    bot.send_message(message.chat.id,
                     f"Текущее: {user_calculations[message.chat.id]}",
                     reply_markup=calcmarkup)


def handle_calculator_digit(message):
    """Добавление цифры"""
    user_calculations[message.chat.id] += message.text
    bot.send_message(message.chat.id,
                     f"Текущее: {user_calculations[message.chat.id]}",
                     reply_markup=calcmarkup)


def handle_calculator_special(message):
    """Добавление спецоператора (^, !, %)"""
    user_calculations[message.chat.id] += message.text
    bot.send_message(message.chat.id,
                     f"Текущее: {user_calculations[message.chat.id]}",
                     reply_markup=calcmarkup)


def handle_calculator_sqrt(message):
    """Добавление квадратного корня"""
    user_calculations[message.chat.id] += "√("
    bot.send_message(message.chat.id,
                     "Пример: √(9)",
                     reply_markup=calcmarkup)