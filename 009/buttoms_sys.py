#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
user_states = {}  # Глобальный словарь состояний


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

def handle_passwords(message):
    """Обработчик меню паролей"""
    try:
        bot.send_message(message.chat.id,
                         "🔐 Управление паролями:",
                         reply_markup=passmarkup)
        log_action(message.chat.id, "Открыта функция паролей")
    except Exception as e:
        error_msg = f"Ошибка в меню паролей: {str(e)}"
        logger.error(error_msg)
        bot.reply_to(message, "⚠ Ошибка при открытии меню паролей")
        log_action(message.chat.id, error_msg, is_error=True)


def handle_addpass(message):
    user_states[message.chat.id] = 'awaiting_service'
    """Начало процесса добавления пароля"""
    try:
        # Удаляем предыдущие обработчики
        bot.clear_step_handler(message)

        msg = bot.send_message(message.chat.id,
                               "Введите название сервиса (например: Google):",
                               reply_markup=types.ReplyKeyboardRemove())

        # Регистрируем следующий шаг с явным указанием фильтров
        bot.register_next_step_handler(
            msg,
            process_service_step,
            timeout=30
        )
        log_action(message.chat.id, "Начато добавление пароля")
    except Exception as e:
        error_msg = f"Ошибка при добавлении пароля: {str(e)}"
        logger.error(error_msg)
        bot.reply_to(message, "⚠ Ошибка при добавлении пароля", reply_markup=passmarkup)
        log_action(message.chat.id, error_msg, is_error=True)

@bot.message_handler(func=lambda m: user_states.get(m.chat.id) == 'awaiting_service')
def process_service(message):
    # Обработка ввода сервиса
    user_states[message.chat.id] = 'awaiting_password'

def process_service_step(message):
    """Обработка ввода сервиса"""
    try:
        logger.info(f"Обработка сервиса: {message.text}")

        # Проверка на команду возврата в меню
        if message.text == "🔙 В меню":
            handle_menu(message)
            return

        # Проверка на другие команды
        if message.text.startswith('/'):
            bot.clear_step_handler(message)
            return

        # Валидация ввода
        service = message.text.strip()
        if not service:
            bot.send_message(message.chat.id,
                             "❌ Название сервиса не может быть пустым",
                             reply_markup=passmarkup)
            return

        if len(service) > 50:
            bot.send_message(message.chat.id,
                             "❌ Слишком длинное название (макс. 50 символов)",
                             reply_markup=passmarkup)
            return

        # Запрос пароля
        msg = bot.send_message(message.chat.id,
                               f"Введите пароль для {service}:",
                               reply_markup=types.ForceReply())

        # Регистрируем следующий шаг
        bot.register_next_step_handler(
            msg,
            lambda m: process_password_step(m, {'user_id': message.chat.id, 'service': service}),
            timeout=30
        )

    except Exception as e:
        logger.error(f"Ошибка в process_service_step: {str(e)}")
        bot.send_message(message.chat.id,
                         "⚠ Ошибка обработки. Попробуйте снова.",
                         reply_markup=passmarkup)


def process_password_step(message, user_data):
    """Обработка ввода пароля и сохранение в БД"""
    try:
        if not message.text or len(message.text) > 100:
            bot.send_message(message.chat.id,
                             "Пароль должен быть от 1 до 100 символов",
                             reply_markup=passmarkup)
            return

        password = message.text.strip()
        conn = db.get_connection()
        if not conn:
            bot.send_message(message.chat.id,
                             "⏳ Сервис временно недоступен. Попробуйте позже.",
                             reply_markup=passmarkup)
            return

        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO passwords (user_id, service, password, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (
            user_data['user_id'],
            user_data['service'],
            password,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()

        bot.send_message(message.chat.id,
                         f"✅ Пароль для {user_data['service']} успешно сохранен!",
                         reply_markup=passmarkup)
        log_action(user_data['user_id'],
                   f"Добавлен пароль для сервиса: {user_data['service']}")
    except Exception as e:
        error_msg = f"Ошибка при сохранении пароля: {str(e)}"
        logger.error(error_msg)
        bot.reply_to(message, "⚠ Ошибка при сохранении пароля")
        log_action(user_data['user_id'], error_msg, is_error=True)
    finally:
        if conn:
            conn.close()


def handle_mypass(message):
    """Показывает сохраненные пароли пользователя"""
    try:
        conn = db.get_connection()
        if not conn:
            bot.send_message(message.chat.id,
                             "⏳ Сервис временно недоступен. Попробуйте позже.",
                             reply_markup=passmarkup)
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
            bot.send_message(message.chat.id,
                             "🔍 У вас нет сохраненных паролей.",
                             reply_markup=passmarkup)
            return

        response = "🔑 Ваши сохраненные пароли:\n\n"
        for item in passwords:
            response += f"🏷 Сервис: {item['service']}\n"
            response += f"🔒 Пароль: {item['password']}\n"
            response += f"⏱ Добавлен: {item['timestamp']}\n\n"

        bot.send_message(message.chat.id, response, reply_markup=passmarkup)
        log_action(message.chat.id, "Просмотр сохраненных паролей")
    except Exception as e:
        error_msg = f"Ошибка при получении паролей: {str(e)}"
        logger.error(error_msg)
        bot.reply_to(message, "⚠ Ошибка при получении паролей")
        log_action(message.chat.id, error_msg, is_error=True)
    finally:
        if conn:
            conn.close()