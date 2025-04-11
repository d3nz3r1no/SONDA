import logging
from telebot import types
from db import db
from cmd import bot, log_action
from buttoms import passwords_markup
from datetime import datetime

logger = logging.getLogger(__name__)

def handle_passwords_start(message):
    bot.send_message(message.chat.id,
                     "🔐 Менеджер паролей. Выберите действие:",
                     reply_markup=passwords_markup)
    log_action(message.chat.id, "Открыт менеджер паролей")


def handle_add_password(message):
    try:
        msg = bot.send_message(message.chat.id,
                               "Введите данные в формате:\n"
                               "<сервис> <логин> <пароль> <примечание(опционально)>\n\n"
                               "Пример: Gmail mymail@gmail.com mypassword123 почта для работы",
                               reply_markup=types.ForceReply())

        bot.register_next_step_handler(msg, process_password_input)
        logger.info(f"Начато добавление пароля для {message.chat.id}")

    except Exception as e:
        logger.error(f"Ошибка в handle_add_password: {str(e)}")
        bot.send_message(message.chat.id, "❌ Ошибка. Попробуйте позже.")


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