from telebot import TeleBot, types
from database.models import Log, User
from utils.logger import log_action
from config import ADMIN_ID
from database.db import handle_db_errors
from database.decorators import handle_db_errors, admin_required


@handle_db_errors
def register_admin_handlers(bot: TeleBot):
    """Регистрирует обработчики административных команд"""

    @bot.message_handler(commands=['logs'], chat_ids=[ADMIN_ID])
    def show_system_logs(message):
        """Показывает системные логи (только для админа)"""
        try:
            logs = Log.get_all_logs(limit=10)
            response = "📃 Последние 10 действий в системе:\n\n"
            for log in logs:
                response += f"▫ {log['timestamp']}: {log['action']}\n"

            bot.reply_to(message, response)
            log_action(message.chat.id, "Просмотр логов администратором")

        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка: {e}")
            log_action(ADMIN_ID, f"Ошибка при показе логов: {str(e)}", is_error=True)

    @bot.message_handler(commands=['users'], chat_ids=[ADMIN_ID])
    def show_users_stats(message):
        """Показывает статистику пользователей (только для админа)"""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()

                # Получаем общее количество пользователей
                cursor.execute("SELECT COUNT(*) FROM users")
                total_users = cursor.fetchone()[0]

                # Получаем количество новых пользователей за последние 7 дней
                cursor.execute('''
                    SELECT COUNT(*) 
                    FROM users 
                    WHERE registration_date >= datetime('now', '-7 days')
                ''')
                new_users = cursor.fetchone()[0]

                response = (
                    "📊 Статистика пользователей:\n\n"
                    f"• Всего пользователей: {total_users}\n"
                    f"• Новых за неделю: {new_users}\n"
                    f"• Последний вход: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )

                bot.reply_to(message, response)
                log_action(message.chat.id, "Просмотр статистики пользователей")

        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка: {e}")
            log_action(ADMIN_ID, f"Ошибка статистики: {str(e)}", is_error=True)

    @bot.message_handler(commands=['broadcast'], chat_ids=[ADMIN_ID])
    def broadcast_message(message):
        """Рассылка сообщения всем пользователям (только для админа)"""
        try:
            msg = bot.reply_to(message, "Введите сообщение для рассылки:")
            bot.register_next_step_handler(msg, process_broadcast)

        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка: {e}")
            log_action(ADMIN_ID, f"Ошибка рассылки: {str(e)}", is_error=True)

    def process_broadcast(message):
        """Обрабатывает рассылку сообщения"""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT user_id FROM users")
                users = cursor.fetchall()

                for user in users:
                    try:
                        bot.send_message(user[0], f"📢 Рассылка:\n\n{message.text}")
                    except Exception as e:
                        log_action(user[0], f"Не удалось отправить рассылку: {str(e)}", is_error=True)

                bot.reply_to(message, f"✅ Сообщение отправлено {len(users)} пользователям")
                log_action(message.chat.id, f"Рассылка: {message.text[:50]}...")

        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка рассылки: {e}")
            log_action(ADMIN_ID, f"Ошибка рассылки: {str(e)}", is_error=True)