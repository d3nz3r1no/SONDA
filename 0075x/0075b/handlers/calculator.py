from telebot import types
import math
from database.models import Calculation
from utils.logger import log_action
from config import DB_NAME
from database.db import handle_db_errors
from database.decorators import handle_db_errors, admin_required

# Глобальный словарь для хранения текущих вычислений пользователей
user_calculations = {}


def safe_calc(expression: str) -> str:
    """
    Безопасное вычисление математических выражений с проверкой ввода
    """
    try:
        # Проверка на пустое выражение
        if not expression or expression.isspace():
            return "Пустое выражение"

        # Проверка на простое число
        if expression.replace('.', '', 1).isdigit():
            return expression

        # Проверка на незакрытые скобки
        if expression.count('(') > expression.count(')'):
            return "Ошибка: не хватает закрывающей скобки"

        # Проверка безопасности
        if '__' in expression or any(op * 2 in expression for op in '+-*/^'):
            return "Недопустимая операция"

        # Проверка длины
        if len(expression) > 50:
            return "Слишком длинное выражение"

        # Разрешенные символы
        allowed_chars = set('0123456789.+-*/()^√!% ')
        if not all(c in allowed_chars for c in expression):
            return "Недопустимые символы"

        # Замена операторов на Python-синтаксис
        expr = (expression
                .replace('^', '**')
                .replace('√(', 'math.sqrt(')
                .replace('%', '/100'))

        # Обработка факториала
        i = 0
        while i < len(expr):
            if expr[i] == '!':
                if i == 0 or not expr[i - 1].isdigit():
                    return "Неверный ввод. Пример: 10!"
                j = i - 1
                while j >= 0 and expr[j].isdigit():
                    j -= 1
                number = expr[j + 1:i]
                replacement = f"math.factorial({number})"
                expr = expr[:j + 1] + replacement + expr[i + 1:]
                i = j + len(replacement)
            else:
                i += 1

        # Вычисление с ограниченным globals
        result = eval(expr, {'__builtins__': None, 'math': math})
        return str(round(result, 5))  # Округление до 5 знаков

    except ZeroDivisionError:
        return "Деление на ноль"
    except ValueError:
        return "Недопустимое значение (например, √-1)"
    except Exception as e:
        return f"Ошибка в выражении: {str(e)}"


@handle_db_errors
def register_calculator_handlers(bot: TeleBot):
    """Регистрирует обработчики для калькулятора"""

    # Клавиатура калькулятора
    calc_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    calc_markup.row("1", "2", "3", "/", "√(")
    calc_markup.row("4", "5", "6", "*", "^")
    calc_markup.row("7", "8", "9", "+", "!")
    calc_markup.row("0", ".", "res", "-", "%")
    calc_markup.row("🔙 В меню", "Стереть", "История 📜", "Повторить ♻")

    @bot.message_handler(func=lambda m: m.text == "➗ Калькулятор")
    def start_calculator(message):
        """Запуск калькулятора"""
        user_calculations[message.chat.id] = ""
        bot.send_message(message.chat.id, "Режим калькулятора...", reply_markup=calc_markup)
        log_action(message.chat.id, "Открыт калькулятор")

    @bot.message_handler(func=lambda m: m.chat.id in user_calculations)
    def handle_calculator_input(message):
        """Обработка всех действий в калькуляторе"""
        user_id = message.chat.id

        if message.text == "🔙 В меню":
            del user_calculations[user_id]
            bot.send_message(user_id, "Главное меню:", reply_markup=main_markup)
            return

        elif message.text == "Стереть":
            user_calculations[user_id] = ""
            bot.send_message(user_id, "Калькулятор очищен.\nТекущее: 0", reply_markup=calc_markup)
            return

        elif message.text == "История 📜":
            history = Calculation.get_history(user_id)
            if not history:
                bot.send_message(user_id, "📭 История вычислений пуста", reply_markup=calc_markup)
                return

            response = "📚 Ваши последние 5 вычислений:\n\n"
            for expr, result, time in history:
                response += f"➤ {expr} = {result}\n   ⌚ {time}\n\n"
            bot.send_message(user_id, response, reply_markup=calc_markup)
            return

        elif message.text == "Повторить ♻":
            last_calc = Calculation.get_last(user_id)
            if last_calc:
                user_calculations[user_id] = last_calc['expression']
                bot.send_message(user_id,
                                 f"↩ Повтор: {last_calc['expression']}\nТекущее: {last_calc['expression']}",
                                 reply_markup=calc_markup)
            else:
                bot.send_message(user_id, "История вычислений пуста", reply_markup=calc_markup)
            return

        elif message.text == "res":
            if not user_calculations.get(user_id) or not user_calculations[user_id].strip():
                bot.send_message(user_id, "Введите выражение сначала", reply_markup=calc_markup)
                return

            expression = user_calculations[user_id].strip()

            # Автодобавление закрывающей скобки для корня
            if '√(' in expression and expression.count('(') > expression.count(')'):
                expression += ")"
                user_calculations[user_id] = expression

            result = safe_calc(expression)

            if not result.startswith("Ошибка"):
                Calculation.add(user_id, expression, result)
                log_action(user_id, f"Вычисление: {expression} = {result}")

            bot.send_message(user_id, f"Результат: {result}", reply_markup=calc_markup)
            return

        # Обработка цифр и операторов
        elif message.text in ["+", "-", "*", "/"]:
            user_calculations[user_id] += f" {message.text} "
        elif message.text.isdigit() or message.text == ".":
            user_calculations[user_id] += message.text
        elif message.text in ["^", "!", "%"]:
            user_calculations[user_id] += message.text
        elif message.text == "√(":
            user_calculations[user_id] += "√("
            bot.send_message(user_id,
                             "Пример: √(9) = 3\nНе забудьте закрыть скобку!",
                             reply_markup=calc_markup)
            return

        bot.send_message(user_id, f"Текущее: {user_calculations[user_id]}", reply_markup=calc_markup)