import logging
from datetime import datetime
from db import db
from cmd import bot, log_action
from buttoms import *
from calc_sys import safe_calc
import sqlite3
from telebot import types

logger = logging.getLogger(__name__)

# Глобальный словарь для хранения текущих вычислений
user_calculations = {}

def get_time():
    """Возвращает форматированное текущее время"""
    return datetime.now().strftime("%H:%M:%S")

@bot.message_handler(func=lambda message: True)
def debug_all_messages(message):
    print(f"Получено сообщение: {message.text} от {message.chat.id}")

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
        elif message.text == "🔒 Пароли":
            handle_passwords(message)
        elif message.text == "🔒 Добавить пароль":
            handle_addpass(message)
        elif message.text == "📂 Мои пароли":
            handle_mypass(message)
        elif message.text == "🔙 В меню":
            handle_menu(message)
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
        "Версия: 0.0.9"
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


# Глобальный словарь для хранения временных данных
user_temp_data = {}

def handle_passwords(message):
    """Обработчик меню паролей"""
    try:
        bot.send_message(
            message.chat.id,
            "🔐 Выберите действие с паролями:",
            reply_markup=passmarkup
        )
        log_action(message.chat.id, "Открыто меню паролей")
    except Exception as e:
        logger.error(f"Ошибка в handle_passwords: {str(e)}")
        bot.reply_to(message, "⚠ Ошибка при открытии меню паролей")


def handle_addpass(message):
    """Начало процесса добавления пароля"""
    try:
        msg = bot.send_message(
            message.chat.id,
            "Введите название сервиса (например: Google):",
            reply_markup=cancel_markup
        )
        bot.register_next_step_handler(msg, process_service_name)
    except Exception as e:
        logger.error(f"Ошибка в handle_addpass: {str(e)}")
        bot.reply_to(message, "⚠ Ошибка при начале добавления пароля", reply_markup=passmarkup)


def process_service_name(message):
    """Обработка ввода названия сервиса"""
    try:
        if message.text.lower() == '❌ отмена':
            bot.send_message(message.chat.id, "Действие отменено", reply_markup=passmarkup)
            return

        # Сохраняем название сервиса во временное хранилище
        user_temp_data[message.chat.id] = {'service': message.text}

        msg = bot.send_message(
            message.chat.id,
            f"Введите пароль для сервиса '{message.text}':",
            reply_markup=cancel_markup
        )
        bot.register_next_step_handler(msg, process_password_input)
    except Exception as e:
        logger.error(f"Ошибка в process_service_name: {str(e)}")
        bot.reply_to(message, "⚠ Ошибка при обработке названия сервиса", reply_markup=passmarkup)


def process_password_input(message):
    """Обработка ввода пароля и сохранение в БД"""
    try:
        if message.text.lower() == '❌ отмена':
            bot.send_message(message.chat.id, "Действие отменено", reply_markup=passmarkup)
            return

        user_id = message.chat.id
        service = user_temp_data.get(user_id, {}).get('service')
        password = message.text

        if not service:
            raise ValueError("Не найдено название сервиса")

        if save_password_to_db(user_id, service, password):
            bot.send_message(
                user_id,
                f"✅ Пароль для '{service}' успешно сохранен!",
                reply_markup=passmarkup
            )
            log_action(user_id, f"Добавлен пароль для сервиса: {service}")
        else:
            raise Exception("Не удалось сохранить пароль в БД")

    except Exception as e:
        logger.error(f"Ошибка в process_password_input: {str(e)}")
        bot.reply_to(message, f"⚠ Ошибка при сохранении пароля: {str(e)}", reply_markup=passmarkup)
    finally:
        # Очищаем временные данные
        user_temp_data.pop(user_id, None)


def handle_mypass(message):
    """Показывает сохраненные пароли пользователя"""
    try:
        conn = db.get_connection()
        if not conn:
            bot.send_message(
                message.chat.id,
                "⏳ Сервис временно недоступен. Попробуйте позже.",
                reply_markup=passmarkup
            )
            return

        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT service, password, timestamp 
            FROM passwords 
            WHERE user_id = ?
            ORDER BY pass_id DESC
        ''', (message.chat.id,))

        passwords = cursor.fetchall()

        if not passwords:
            bot.send_message(
                message.chat.id,
                "🔍 У вас нет сохраненных паролей.",
                reply_markup=passmarkup
            )
            return

        response = "🔑 Ваши сохраненные пароли:\n\n"
        for item in passwords:
            response += f"🏷 Сервис: {item['service']}\n"
            response += f"🔒 Пароль: ||{item['password']}||\n"
            response += f"⏱ Добавлен: {item['timestamp']}\n\n"

        bot.send_message(
            message.chat.id,
            response,
            reply_markup=passmarkup,
            parse_mode='MarkdownV2'  # Для скрытия пароля
        )
        log_action(message.chat.id, "Просмотр списка паролей")

    except Exception as e:
        logger.error(f"Ошибка в handle_mypass: {str(e)}")
        bot.reply_to(message, "⚠ Ошибка при получении паролей", reply_markup=passmarkup)
    finally:
        if conn:
            conn.close()


def save_password_to_db(user_id, service, password):
    """Улучшенная функция сохранения пароля в БД"""
    try:
        conn = db.get_connection()
        if not conn:
            return False

        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO passwords (user_id, service, password, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (
            user_id,
            service,
            password,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения пароля: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()