import logging
from telebot import types
from db import db
from properties import bot
from buttoms import passwords_markup
from datetime import datetime
from log_action import log_action

logger = logging.getLogger(__name__)

# Словарь для отслеживания состояния пользователей
user_states = {}


def handle_passwords_start(message):
    bot.send_message(message.chat.id,
                     "🔐 Менеджер паролей. Выберите действие:",
                     reply_markup=passwords_markup)
    log_action(message.chat.id, "Открыт менеджер паролей")


def handle_add_password(message):
    try:
        # Устанавливаем состояние "добавление пароля"
        user_states[message.chat.id] = "adding_password"

        bot.send_message(message.chat.id,
                         "Введите данные в формате:\n"
                         "<сервис> <логин> <пароль> <примечание(опционально)>\n\n"
                         "Пример: Gmail mymail@gmail.com mypassword123 почта для работы",
                         reply_markup=types.ForceReply())

        logger.info(f"Начато добавление пароля для {message.chat.id}")

    except Exception as e:
        logger.error(f"Ошибка в handle_add_password: {str(e)}")
        bot.send_message(message.chat.id, "❌ Ошибка. Попробуйте позже.")


def handle_message(message):
    """Главный обработчик сообщений для паролей"""
    if message.chat.id in user_states and user_states[message.chat.id] == "adding_password":
        # Удаляем состояние перед обработкой
        del user_states[message.chat.id]
        process_password_input(message)
    else:
        # Если это не ответ на запрос пароля, игнорируем
        pass


def process_password_input(message):
    try:
        logger.info(f"Обработка ввода: {message.text}")

        parts = message.text.split(maxsplit=3)
        if len(parts) < 3:
            raise ValueError("Недостаточно данных. Нужно: сервис логин пароль")

        service = parts[0]
        username = parts[1]
        password = parts[2]
        notes = parts[3] if len(parts) > 3 else ""

        # Сохраняем в БД
        conn = None
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO passwords (user_id, service_name, username, password, notes, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                message.chat.id,
                service,
                username,
                password,
                notes,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()

            bot.send_message(message.chat.id,
                             "✅ Пароль успешно сохранен!",
                             reply_markup=passwords_markup)
            logger.info(f"Пароль сохранен для {message.chat.id}")

        except Exception as e:
            logger.error(f"Ошибка БД: {str(e)}")
            bot.send_message(message.chat.id,
                             "❌ Ошибка сохранения. Попробуйте позже.",
                             reply_markup=passwords_markup)
        finally:
            if conn:
                conn.close()

    except Exception as e:
        logger.error(f"Ошибка обработки: {str(e)}")
        bot.send_message(message.chat.id,
                         f"❌ Ошибка: {str(e)}\n\n"
                         "Правильный формат:\n"
                         "<сервис> <логин> <пароль> <примечание>",
                         reply_markup=passwords_markup)


def handle_show_passwords(message):
    """Показывает сохраненные пароли пользователя"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT service_name, username, password, notes 
            FROM passwords 
            WHERE user_id = ?
            ORDER BY service_name
        ''', (message.chat.id,))

        passwords = cursor.fetchall()

        if not passwords:
            bot.send_message(message.chat.id,
                             "📭 У вас нет сохраненных паролей",
                             reply_markup=passwords_markup)
            return

        response = "🔐 Ваши сохраненные пароли:\n\n"
        for pwd in passwords:
            response += f"🏷 Сервис: {pwd[0]}\n"
            response += f"👤 Логин: {pwd[1]}\n"
            response += f"🔑 Пароль: ||{pwd[2]}||\n"
            if pwd[3]:
                response += f"📝 Примечание: {pwd[3]}\n"
            response += "――――――――――\n"

        bot.send_message(message.chat.id,
                         response,
                         reply_markup=passwords_markup,
                         parse_mode='MarkdownV2')
        log_action(message.chat.id, "Просмотр списка паролей")

    except Exception as e:
        logger.error(f"Ошибка получения паролей: {str(e)}")
        bot.send_message(message.chat.id,
                         "❌ Ошибка при загрузке паролей",
                         reply_markup=passwords_markup)
        log_action(message.chat.id, "Ошибка просмотра паролей", is_error=True)
    finally:
        if conn:
            conn.close()