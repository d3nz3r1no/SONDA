from telebot import TeleBot
from config import TOKEN
from handlers import commands, calculator, admin
from database.db import init_db

def main():
    # Инициализация
    init_db()
    bot = TeleBot(TOKEN)

    # Регистрация обработчиков
    commands.register_handlers(bot)
    calculator.register_handlers(bot)
    admin.register_handlers(bot)

    # Запуск бота
    print("Бот запущен!")
    bot.polling()

if __name__ == "__main__":
    main()