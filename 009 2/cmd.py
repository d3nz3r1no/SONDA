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
    """Показывает историю вычислений пользователя"""
    conn = None
    try:
        # Логируем начало выполнения команды
        logger.info(f"Запрос истории от пользователя {message.chat.id}")

        conn = db.get_connection()
        if not conn:
            error_msg = "Не удалось подключиться к БД"
            logger.error(error_msg)
            bot.reply_to(message, "⏳ Проблемы с базой данных. Попробуйте позже.")
            return

        # Проверяем существование таблицы calculations
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='calculations'")
        if not cursor.fetchone():
            error_msg = "Таблица calculations не существует"
            logger.error(error_msg)
            bot.reply_to(message, "⚠ Внутренняя ошибка: таблица вычислений не найдена")
            return

        # Получаем историю вычислений
        cursor.execute('''
            SELECT expression, result, timestamp 
            FROM calculations
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 5
        ''', (message.chat.id,))

        history = cursor.fetchall()

        if not history:
            logger.info(f"Пустая история для пользователя {message.chat.id}")
            bot.reply_to(message, "📭 У вас пока нет истории вычислений")
            return

        # Формируем ответ
        response = "📚 Ваши последние вычисления:\n\n"
        for item in history:
            response += f"➤ {item['expression']} = {item['result']}\n"
            response += f"   ⌚ {item['timestamp']}\n\n"

        bot.reply_to(message, response)
        logger.info(f"Успешно показана история для {message.chat.id}")

    except sqlite3.Error as e:
        error_msg = f"Ошибка SQL: {str(e)}"
        logger.error(error_msg)
        bot.reply_to(message, "⚠ Ошибка при работе с базой данных")

    except Exception as e:
        error_msg = f"Неожиданная ошибка: {str(e)}"
        logger.error(error_msg)
        bot.reply_to(message, "⚠ Произошла непредвиденная ошибка")

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