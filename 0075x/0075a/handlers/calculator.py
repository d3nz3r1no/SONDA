from telebot import TeleBot
from utils.safety import safe_calc
from utils.logger import log_action

def register_handlers(bot: TeleBot):
    @bot.message_handler(func=lambda m: m.text == "➗ Калькулятор")
    def start_calculator(message):
        """Запуск калькулятора."""
        log_action(message.chat.id, "Открыт калькулятор")
        bot.send_message(message.chat.id, "Введите выражение:")

    @bot.message_handler(func=lambda m: m.text.startswith('='))
    def calculate(message):
        """Обработка вычислений."""
        expr = message.text[1:].strip()
        result = safe_calc(expr)
        bot.reply_to(message, f"Результат: {result}")