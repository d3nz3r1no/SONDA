import logging
from datetime import datetime
from telebot import types
from db import db
from cmd import bot, log_action
from buttoms import passwords_markup

logger = logging.getLogger(__name__)


def handle_passwords_start(message):
    """Обработчик входа в меню паролей"""
    bot.send_message(message.chat.id,
                     "🔐 Менеджер паролей. Выберите действие:",
                     reply_markup=passwords_markup)
    log_action(message.chat.id, "Открыт менеджер паролей")


def handle_add_password(message):
    """Обработчик добавления пароля"""
    msg = bot.send_message(message.chat.id,
                           "Введите данные в формате:\n"
                           "<сервис> <логин> <пароль> <примечание(опционально)>\n\n"
                           "Пример: Gmail mymail@gmail.com mypassword123 почта для работы",
                           reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, process_password_input)


def process_password_input(message):
    """Обработка введенных данных пароля"""
    try:
        parts = message.text.split(maxsplit=3)
        if len(parts) < 3:
            raise ValueError("Недостаточно данных")

        service = parts[0]
        username = parts[1]
        password = parts[2]
        notes = parts[3] if len(parts) > 3 else ""

        # Сохраняем в БД
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
        log_action(message.chat.id, f"Добавлен пароль для {service}")

    except Exception as e:
        logger.error(f"Ошибка добавления пароля: {str(e)}")
        bot.send_message(message.chat.id,
                         "❌ Ошибка формата. Попробуйте еще раз.",
                         reply_markup=passwords_markup)
        log_action(message.chat.id, "Ошибка добавления пароля", is_error=True)
    finally:
        if conn:
            conn.close()


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