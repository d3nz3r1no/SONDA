from telebot import TeleBot, types
from datetime import datetime
from database.models import User, Log, Calculation
from utils.logger import log_action
from config import ADMIN_ID
from database.db import handle_db_errors
from database.decorators import handle_db_errors, admin_required

# Инициализация клавиатур
main_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_markup.add("👋 Привет", "❓ Помощь")

hello_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
hello_markup.add("Обо мне ❓", "⚙️ Меню")

menu_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
menu_markup.add("➗ Калькулятор", "🔒 Пароли")


@handle_db_errors
def register_command_handlers(bot: TeleBot):
    """Регистрирует обработчики основных команд"""

    @bot.message_handler(commands=['start'])
    def handle_start(message):
        """Обработчик команды /start"""
        try:
            # Регистрация пользователя
            User.create(
                message.chat.id,
                message.from_user.username,
                message.from_user.first_name,
                message.from_user.last_name
            )

            # Логирование
            Log.add(message.chat.id, "Команда /start")

            # Ответ пользователю
            bot.send_message(
                message.chat.id,
                "Успешный старт бота.\nГруппа тестировщиков - https://t.me/sondatest",
                reply_markup=main_markup
            )
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Бот запущен пользователем {message.chat.id}")

        except Exception as e:
            bot.reply_to(message, "⚠ Произошла ошибка при регистрации. Пожалуйста, попробуйте позже.")
            Log.add(message.chat.id, f"Ошибка при регистрации: {str(e)}", is_error=True)

    @bot.message_handler(commands=['help'])
    def handle_help(message):
        """Обработчик команды /help"""
        help_text = """
        Доступные команды:
        /start - Запустить бота
        /help - Показать это сообщение
        /infobot - Информация о боте
        /mylogs - Ваши последние действия
        /clearmyhistory - Очистить вашу историю"""

        bot.reply_to(message, help_text)
        Log.add(message.chat.id, "Запрошена помощь")

    @bot.message_handler(commands=['infobot'])
    def handle_infobot(message):
        """Обработчик команды /infobot"""
        info_text = """
        Версия SONDA 0.0.74
        Канал обновлений: https://t.me/sondachanel
        Группа поддержки: https://t.me/sondatest"""

        bot.reply_to(message, info_text)
        Log.add(message.chat.id, "Запрошена информация о боте")

    @bot.message_handler(commands=['mylogs'])
    def handle_mylogs(message):
        """Обработчик команды /mylogs"""
        try:
            logs = Log.get_user_logs(message.chat.id)

            if not logs:
                bot.reply_to(message, "📭 Ваша история действий пуста")
                return

            response = "📖 Ваши последние действия:\n\n"
            for log in logs:
                response += f"• {log['timestamp']}: {log['action']}\n"

            bot.reply_to(message, response)
            Log.add(message.chat.id, "Просмотр своих логов")

        except Exception as e:
            bot.reply_to(message, f"⚠ Ошибка: {str(e)}")
            Log.add(0, f"Ошибка при запросе логов: {str(e)}", is_error=True)

    @bot.message_handler(commands=['clearmyhistory'])
    def handle_clear_history(message):
        """Обработчик команды /clearmyhistory"""
        try:
            Calculation.clear_history(message.chat.id)
            Log.add(message.chat.id, "Очищена история вычислений")
            bot.reply_to(message, "✅ Ваша история вычислений была очищена")

        except Exception as e:
            bot.reply_to(message, f"⚠ Ошибка при очистке истории: {str(e)}")
            Log.add(0, f"Ошибка очистки истории: {str(e)}", is_error=True)

    @bot.message_handler(content_types=['text'])
    def handle_text_messages(message):
        """Обработчик текстовых сообщений (кнопки)"""
        if message.text == "👋 Привет":
            bot.reply_to(message,
                         "Привет, я SONDA - Бот который может очень многое. Пользуйся мной во благо себя.",
                         reply_markup=hello_markup)
            Log.add(message.chat.id, "Нажата кнопка '👋 Привет'")

        elif message.text == "❓ Помощь":
            handle_help(message)
            Log.add(message.chat.id, "Нажата кнопка '❓ Помощь'")

        elif message.text == "Обо мне ❓":
            bot.reply_to(message,
                         "SONDA - это бот, а название - совмещение имён Даня и Соня.\n"
                         "Пока у меня нет никаких возможностей, но вскоре они появятся.",
                         reply_markup=main_markup)
            Log.add(message.chat.id, "Нажата кнопка 'Обо мне ❓'")

        elif message.text == "⚙️ Меню":
            bot.reply_to(message, "Основной функционал:", reply_markup=menu_markup)
            Log.add(message.chat.id, "Нажата кнопка '⚙️ Меню'")