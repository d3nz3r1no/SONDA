from telebot import TeleBot, types
from datetime import datetime
import sqlite3
from utils.logger import log_action
from config import DB_NAME
from database.db import handle_db_errors
from database.decorators import handle_db_errors, admin_required

# Инициализация клавиатуры для паролей
passwords_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
passwords_markup.row("🔐 Добавить пароль", "📋 Список паролей")
passwords_markup.row("✏️ Изменить пароль", "❌ Удалить пароль")
passwords_markup.row("🔙 В меню")

@handle_db_errors
def register_password_handlers(bot: TeleBot):
    """Регистрирует обработчики для работы с паролями"""

    # Создание таблицы паролей при первом запуске
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('''
        CREATE TABLE IF NOT EXISTS passwords (
            pass_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            service TEXT,
            login TEXT,
            password TEXT,
            notes TEXT,
            timestamp TEXT,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        ''')
        conn.commit()

    @bot.message_handler(func=lambda m: m.text == "🔒 Пароли")
    def handle_passwords(message):
        """Обработчик кнопки паролей"""
        user_calculations.pop(message.chat.id, None)  # Очистка калькулятора
        bot.send_message(
            message.chat.id,
            "🔐 Менеджер паролей. Выберите действие:",
            reply_markup=passwords_markup
        )
        log_action(message.chat.id, "Открыт менеджер паролей")

    @bot.message_handler(func=lambda m: m.text == "🔐 Добавить пароль")
    def handle_add_password(message):
        """Добавление нового пароля"""
        msg = bot.reply_to(message, "Введите данные в формате:\n\n<Сервис> <Логин> <Пароль> [Примечание]")
        bot.register_next_step_handler(msg, process_add_password)

    def process_add_password(message):
        """Обработка добавления пароля"""
        try:
            parts = message.text.split(maxsplit=3)
            if len(parts) < 3:
                raise ValueError("Недостаточно данных")

            service, login, password = parts[:3]
            notes = parts[3] if len(parts) > 3 else ""

            with sqlite3.connect(DB_NAME) as conn:
                conn.execute(
                    "INSERT INTO passwords (user_id, service, login, password, notes, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                    (message.chat.id, service, login, password, notes, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                conn.commit()

            bot.reply_to(
                message.chat.id,
                f"✅ Пароль для {service} успешно сохранен!",
                reply_markup=passwords_markup
            )
            log_action(message.chat.id, f"Добавлен пароль для {service}")

        except Exception as e:
            bot.reply_to(
                message.chat.id,
                f"❌ Ошибка: {str(e)}\nПопробуйте еще раз.",
                reply_markup=passwords_markup
            )
            log_action(message.chat.id, f"Ошибка добавления пароля: {str(e)}", is_error=True)

    @bot.message_handler(func=lambda m: m.text == "📋 Список паролей")
    def handle_list_passwords(message):
        """Показ списка сохраненных паролей"""
        try:
            with sqlite3.connect(DB_NAME) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT service, login, timestamp FROM passwords WHERE user_id = ? ORDER BY timestamp DESC",
                    (message.chat.id,))
                passwords = cursor.fetchall()

            if not passwords:
                bot.reply_to(
                    message.chat.id,
                    "📭 У вас нет сохраненных паролей",
                    reply_markup=passwords_markup
                )
                return

            response = "📋 Ваши сохраненные пароли:\n\n"
            for pwd in passwords:
                response += f"• {pwd['service']} ({pwd['login']})\n   ⌚ {pwd['timestamp']}\n\n"

            bot.reply_to(
                message.chat.id,
                response,
                reply_markup=passwords_markup
            )
            log_action(message.chat.id, "Просмотр списка паролей")

        except Exception as e:
            bot.reply_to(
                message.chat.id,
                f"❌ Ошибка: {str(e)}",
                reply_markup=passwords_markup
            )
            log_action(message.chat.id, f"Ошибка просмотра паролей: {str(e)}", is_error=True)

    @bot.message_handler(func=lambda m: m.text == "❌ Удалить пароль")
    def handle_delete_password(message):
        """Удаление сохраненного пароля"""
        msg = bot.reply_to(
            message,
            "Введите название сервиса для удаления:",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, process_delete_password)

    def process_delete_password(message):
        """Обработка удаления пароля"""
        try:
            service = message.text.strip()
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM passwords WHERE user_id = ? AND service = ?",
                    (message.chat.id, service))
                conn.commit()

                if cursor.rowcount == 0:
                    raise ValueError("Пароль для указанного сервиса не найден")

            bot.reply_to(
                message.chat.id,
                f"✅ Пароль для {service} удален!",
                reply_markup=passwords_markup
            )
            log_action(message.chat.id, f"Удален пароль для {service}")

        except Exception as e:
            bot.reply_to(
                message.chat.id,
                f"❌ Ошибка: {str(e)}",
                reply_markup=passwords_markup
            )
            log_action(message.chat.id, f"Ошибка удаления пароля: {str(e)}", is_error=True)