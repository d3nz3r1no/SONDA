import logging
import sqlite3
from datetime import datetime
from db import db
from properties import ADMIN_ID
from bot_instance import bot
from buttoms import markup

# Настройка логгера
logger = logging.getLogger(__name__)


def get_time():
    """Возвращает форматированное текущее время"""
    return datetime.now().strftime("%H:%M:%S")


def log_action(user_id, action, is_error=False):
    """Логирует действие в БД и файл логов"""
    try:
        conn = db.get_connection()
        if not conn:
            logger.error("Не удалось подключиться к БД для логирования")
            return False

        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO logs (user_id, action, timestamp)
            VALUES (?, ?, ?)
        ''', (
            user_id,
            f"{'🚨 ' if is_error else ''}{action}",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Ошибка логирования: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()


def is_admin(user_id):
    """Проверяет, является ли пользователь администратором"""
    return user_id == ADMIN_ID


@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Обработчик команды /start с регистрацией пользователя"""
    try:
        conn = db.get_connection()
        if not conn:
            bot.reply_to(message, "⏳ Сервис временно недоступен. Попробуйте позже.")
            return

        cursor = conn.cursor()

        # Проверка и регистрация пользователя
        cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (message.chat.id,))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO users (user_id, username, first_name, last_name, registration_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                message.chat.id,
                message.from_user.username,
                message.from_user.first_name,
                message.from_user.last_name,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()
            logger.info(f"Новый пользователь: {message.from_user.username}")

        # Отправка приветственного сообщения
        welcome_text = (
            "👋 Добро пожаловать!\n"
            "Группа тестировщиков - https://t.me/sondatest\nКанал про меня - https://t.me/sondachanel\n"
            "Используйте /help для просмотра списка команд."
        )

        bot.send_message(
            message.chat.id,
            welcome_text,
            reply_markup=markup
        )

        log_action(message.chat.id, "Команда /start")

    except Exception as e:
        error_msg = f"Ошибка при регистрации: {str(e)}"
        bot.reply_to(message, "⚠ Произошла ошибка. Попробуйте позже.")
        logger.error(error_msg)
        log_action(message.chat.id, error_msg, is_error=True)
    finally:
        if conn:
            conn.close()


@bot.message_handler(commands=['help'])
def send_help(message):
    """Обработчик команды /help"""
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


@bot.message_handler(commands=['mylogs'])
def show_my_logs(message):
    """Показывает последние действия пользователя"""
    try:
        conn = db.get_connection()
        if not conn:
            bot.reply_to(message, "⏳ Сервис временно недоступен.")
            return

        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT action, timestamp FROM logs 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''', (message.chat.id,))

        logs = cursor.fetchall()

        if not logs:
            bot.reply_to(message, "📭 Ваша история действий пуста")
            return

        response = "📖 Ваши последние действия:\n\n"
        for log in logs:
            response += f"• {log['timestamp']}: {log['action']}\n"

        bot.reply_to(message, response)
        log_action(message.chat.id, "Просмотр логов")

    except Exception as e:
        error_msg = f"Ошибка получения логов: {str(e)}"
        bot.reply_to(message, "⚠ Ошибка при получении логов")
        logger.error(error_msg)
        log_action(message.chat.id, error_msg, is_error=True)
    finally:
        if conn:
            conn.close()


@bot.message_handler(commands=['history'])
def show_history(message):
    """Улучшенный обработчик истории с диагностикой"""
    try:
        logger.info(f"Получен /history от {message.chat.id}")

        # Временный ответ для отслеживания
        bot.send_chat_action(message.chat.id, 'typing')

        conn = db.get_connection()
        if not conn:
            logger.error("Нет соединения с БД")
            return bot.reply_to(message, "🔧 Технические неполадки. Попробуйте позже.")

        # Проверка таблицы
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM calculations WHERE user_id=?", (message.chat.id,))
        count = cursor.fetchone()[0]

        if count == 0:
            logger.info(f"Нет записей для {message.chat.id}")
            return bot.reply_to(message, "📭 История вычислений пуста")

        # Получение истории
        cursor.execute('''
            SELECT expression, result, timestamp 
            FROM calculations 
            WHERE user_id=?
            ORDER BY timestamp DESC 
            LIMIT 5
        ''', (message.chat.id,))

        history = cursor.fetchall()
        response = "📝 История вычислений:\n\n" + "\n".join(
            f"{i + 1}. {item[0]} = {item[1]} ({item[2]})"
            for i, item in enumerate(history)
        )

        bot.reply_to(message, response)
        logger.info(f"Успешно показана история для {message.chat.id}")

    except Exception as e:
        logger.error(f"Ошибка в /history: {str(e)}")
        bot.reply_to(message, f"⚠ Ошибка: {str(e)}")
    finally:
        if conn:
            conn.close()


@bot.message_handler(commands=['clearmyhistory'])
def clear_user_history(message):
    """Очищает историю пользователя"""
    try:
        conn = db.get_connection()
        if not conn:
            bot.reply_to(message, "⏳ Сервис временно недоступен.")
            return

        cursor = conn.cursor()

        # Удаление истории вычислений
        cursor.execute('DELETE FROM calculations WHERE user_id = ?', (message.chat.id,))

        # Удаление логов (кроме самой команды очистки)
        cursor.execute('''
            DELETE FROM logs 
            WHERE user_id = ? 
            AND action NOT LIKE '%Очищена история%'
        ''', (message.chat.id,))

        # Логирование действия
        cursor.execute('''
            INSERT INTO logs (user_id, action, timestamp)
            VALUES (?, ?, ?)
        ''', (
            message.chat.id,
            "Очищена история",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()
        bot.reply_to(message, "✅ Ваша история очищена")
        log_action(message.chat.id, "Очистка истории")

    except Exception as e:
        error_msg = f"Ошибка очистки истории: {str(e)}"
        bot.reply_to(message, "⚠ Ошибка при очистке истории")
        logger.error(error_msg)
        log_action(message.chat.id, error_msg, is_error=True)
    finally:
        if conn:
            conn.close()


@bot.message_handler(commands=['logs'])
def show_system_logs(message):
    """Показывает системные логи (только для администратора)"""
    if not is_admin(message.chat.id):
        bot.reply_to(message, "⛔ Доступ запрещен")
        log_action(message.chat.id, "Попытка доступа к системным логам", is_error=True)
        return

    try:
        conn = db.get_connection()
        if not conn:
            bot.reply_to(message, "⏳ Сервис временно недоступен.")
            return

        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id, action, timestamp 
            FROM logs 
            ORDER BY log_id DESC 
            LIMIT 20
        ''')

        logs = cursor.fetchall()

        if not logs:
            bot.reply_to(message, "📭 Логи отсутствуют")
            return

        response = "📃 Последние 20 действий в системе:\n\n"
        for log in logs:
            response += f"👤 {log[0]}: {log[1]}\n"
            response += f"   ⌚ {log[2]}\n\n"

        bot.reply_to(message, response)
        log_action(message.chat.id, "Просмотр системных логов")

    except Exception as e:
        error_msg = f"Ошибка получения системных логов: {str(e)}"
        bot.reply_to(message, "⚠ Ошибка при загрузке логов")
        logger.error(error_msg)
        log_action(ADMIN_ID, error_msg, is_error=True)
    finally:
        if conn:
            conn.close()