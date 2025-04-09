from db import *
from buttoms import *
from log_action import *
from notifyadmin import *

# ==================== ОБРАБОТЧИКИ КОМАНД ====================
@handle_db_errors
@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Обработчик команды /start"""
    try:
        with sqlite3.connect('sonda_bot.db') as conn:
            cursor = conn.cursor()
            # Регистрация нового пользователя
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

            # Логирование запуска
            cursor.execute('''
            INSERT INTO logs (user_id, action, timestamp)
            VALUES (?, ?, ?)
            ''', (message.chat.id, "start", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()

        bot.send_message(
            message.chat.id,
            "Успешный старт бота.\nГруппа тестировщиков - https://t.me/sondatest",
            reply_markup=markup
        )
        print(f"[{get_time()}] Бот запущен пользователем {message.chat.id}")
    except Exception as e:
        bot.reply_to(message, "⚠ Произошла ошибка при регистрации. Пожалуйста, попробуйте позже.")
        log_action(message.chat.id, f"Ошибка при регистрации: {str(e)}", is_error=True)

@bot.message_handler(commands=['mylogs'])  # Логи для пользователей + Защита
def show_my_logs(message):
    """Показывает логи текущего пользователя"""
    try:
        with sqlite3.connect('sonda_bot.db') as conn:
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

        response = "📖 Ваши последние 10 действий:\n\n"
        for log in logs:
            response += f"• {log['timestamp']}: {log['action']}\n"

        bot.reply_to(message, response)
        log_action(message.chat.id, "Запрошена история действий")

    except Exception as e:
        bot.reply_to(message, f"⚠ Ошибка: {str(e)}")
        log_action(0, f"Ошибка при запросе логов: {str(e)}", is_error=True)

# Обработчик команды /help
@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
    Доступные команды:
    /start - Запустить бота
    /help - Команды
    /infobot - Обновления бота
    /mylogs - 10 ваших последних действий
    /clearmyhistory - Удалить вашу историю"""
    bot.reply_to(message, help_text)

# Обработчик команды /infobot
@bot.message_handler(commands=['infobot'])
def send_infobot(message):
    infobot_text = """
    Версия SONDA 0.0.74
    Канал по новостям и обновлениям - https://t.me/sondachanel"""
    bot.reply_to(message, infobot_text)

@handle_db_errors
@bot.message_handler(commands=['logs'])
def show_logs(message):
    if not is_admin(message.chat.id):
        bot.reply_to(message, "⛔ Доступ запрещен")
        log_action(message.chat.id, "Попытка доступа к логам без прав", is_error=True)
        return

    try:
        with sqlite3.connect('sonda_bot.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT action, timestamp FROM logs 
            ORDER BY log_id DESC LIMIT 10
            ''')
            logs = cursor.fetchall()

        response = "📃 Последние 10 действий:\n\n"
        for action, timestamp in logs:
            response += f"▫ {timestamp}: {action}\n"
        bot.reply_to(message, response)
        log_action(message.chat.id, "Просмотр логов администратором")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
        log_action(ADMIN_ID, f"Ошибка при показе логов: {str(e)}", is_error=True)

@handle_db_errors
@bot.message_handler(commands=['history'])
def show_history(message):
    """Показывает историю вычислений"""
    try:
        with sqlite3.connect('sonda_bot.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT expression, result, timestamp FROM calculations
            WHERE user_id = ? ORDER BY calc_id DESC LIMIT 5
            ''', (message.chat.id,))
            history = cursor.fetchall()

        if not history:
            bot.reply_to(message, "📭 История вычислений пуста")
            return

        response = "📚 Ваши последние 5 вычислений:\n\n"
        for expr, result, time in history:
            response += f"➤ {expr} = {result}\n   ⌚ {time}\n\n"
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, "⚠ Не удалось загрузить историю вычислений. Пожалуйста, попробуйте позже.")
        log_action(message.chat.id, f"Ошибка показа истории: {str(e)}", is_error=True)

@handle_db_errors
@bot.message_handler(commands=['clearmyhistory']) # Удаляет историю вычислений и действий пользователя
def clear_user_history(message):
    try:
        with sqlite3.connect('sonda_bot.db') as conn:
            cursor = conn.cursor()
            # Удаляем историю вычислений
            cursor.execute('DELETE FROM calculations WHERE user_id = ?', (message.chat.id,))
            # Удаляем логи пользователя (кроме команды очистки)
            cursor.execute('DELETE FROM logs WHERE user_id = ? AND action != "Очищена история"', (message.chat.id,))
            # Логируем действие
            cursor.execute('''
            INSERT INTO logs (user_id, action, timestamp)
            VALUES (?, ?, ?)
            ''', (
                message.chat.id,
                "Очищена история",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()
        bot.reply_to(message, "✅ Ваша история вычислений и действий была очищена")
    except Exception as e:
        bot.reply_to(message, f"⚠ Ошибка при очистке истории: {str(e)}")
        log_action(0, f"Ошибка очистки истории: {str(e)}", is_error=True)
