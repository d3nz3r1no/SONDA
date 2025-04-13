import math
import sqlite3
import logging
import log_action
from db import db
from datetime import datetime
from properties import bot
from buttoms import calcmarkup, markup

logger = logging.getLogger(__name__)

# Глобальный словарь для хранения текущих вычислений
user_calculations = {}

def save_calculation(user_id, expression, result):
    """Сохраняет вычисление в БД"""
    try:
        conn = db.get_connection()
        if not conn:
            logger.error("Не удалось подключиться к БД для сохранения вычисления")
            return False

        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO calculations (user_id, expression, result, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (
            user_id,
            expression,
            result,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения вычисления: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

def safe_calc(expression):
    """Безопасное вычисление с поддержкой новых операций"""
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
        if len(expression) > 100:
            return "Слишком длинное выражение"

        # Разрешенные символы
        allowed_chars = set('0123456789.+-*/()^√!% ')
        if not all(c in allowed_chars for c in expression):
            return "Недопустимые символы"

        # Замена операторов
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
                if not number:
                    return "Ошибка: факториал только для чисел"
                replacement = f"math.factorial({number})"
                expr = expr[:j + 1] + replacement + expr[i + 1:]
                i = j + len(replacement)
            else:
                i += 1

        # Вычисление
        result = eval(expr, {'__builtins__': None, 'math': math})
        return str(round(result, 5))

    except ZeroDivisionError:
        return "Деление на ноль"
    except ValueError:
        return "Недопустимое значение (например, √-1)"
    except Exception as e:
        return f"Ошибка в выражении: {str(e)}"


def get_last_calculation(user_id):
    """Возвращает последнее вычисление пользователя"""
    try:
        conn = db.get_connection()
        if not conn:
            return None

        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT expression, result 
            FROM calculations
            WHERE user_id = ? 
            ORDER BY calc_id DESC 
            LIMIT 1
        ''', (user_id,))
        return cursor.fetchone()
    except Exception as e:
        print(f"[Ошибка] Не удалось получить вычисление: {e}")
        return None
    finally:
        if conn:
            conn.close()

def handle_calculator_start(message):
    """Обработчик запуска калькулятора"""
    user_calculations[message.chat.id] = ""
    bot.send_message(message.chat.id,
                     "Режим калькулятора. Вводите выражение:",
                     reply_markup=calcmarkup)
    log_action(message.chat.id, "Запущен калькулятор")

def handle_calculator_exit(message):
    """Выход из калькулятора"""
    if message.chat.id in user_calculations:
        del user_calculations[message.chat.id]
    bot.send_message(message.chat.id, "Возврат в меню:", reply_markup=markup)
    log_action(message.chat.id, "Выход из калькулятора")


def show_history(message):
    """Показывает историю вычислений"""
    try:
        conn = db.get_connection()
        if not conn:
            bot.reply_to(message, "⏳ Сервис временно недоступен.")
            return

        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT expression, result, timestamp 
            FROM calculations 
            WHERE user_id = ? 
            ORDER BY calc_id DESC 
            LIMIT 5
        ''', (message.chat.id,))

        history = cursor.fetchall()

        if not history:
            bot.send_message(message.chat.id,
                             "История вычислений пуста",
                             reply_markup=calcmarkup)
            return

        response = "📝 Ваши последние вычисления:\n\n"
        for item in history:
            response += f"▸ {item['expression']} = {item['result']}\n"
            response += f"⏱ {item['timestamp']}\n\n"

        bot.send_message(message.chat.id, response, reply_markup=calcmarkup)
        log_action(message.chat.id, "Просмотр истории в калькуляторе")
    finally:
        if conn:
            conn.close()


def handle_calculator_clear(message):
    """Очистка текущего выражения"""
    user_calculations[message.chat.id] = ""
    bot.send_message(message.chat.id,
                     "Калькулятор очищен. Текущее: 0",
                     reply_markup=calcmarkup)
    log_action(message.chat.id, "Очистка калькулятора")


def handle_calculator_repeat(message):
    """Повтор последнего вычисления"""
    try:
        conn = db.get_connection()
        if not conn:
            bot.send_message(message.chat.id,
                             "⏳ Сервис временно недоступен.",
                             reply_markup=calcmarkup)
            return

        cursor = conn.cursor()
        cursor.execute('''
            SELECT expression 
            FROM calculations 
            WHERE user_id = ? 
            ORDER BY calc_id DESC 
            LIMIT 1
        ''', (message.chat.id,))

        last_calc = cursor.fetchone()

        if last_calc:
            user_calculations[message.chat.id] = last_calc[0]
            bot.send_message(message.chat.id,
                             f"↩ Повтор: {last_calc[0]}",
                             reply_markup=calcmarkup)
        else:
            bot.send_message(message.chat.id,
                             "Нет истории вычислений",
                             reply_markup=calcmarkup)
    finally:
        if conn:
            conn.close()


def handle_calculator_result(message):
    """Вычисление результата"""
    if not user_calculations.get(message.chat.id):
        bot.send_message(message.chat.id,
                         "Введите выражение сначала",
                         reply_markup=calcmarkup)
        return

    expression = user_calculations[message.chat.id].strip()

    # Автодобавление закрывающей скобки для корня
    if '√(' in expression and expression.count('(') > expression.count(')'):
        expression += ")"
        user_calculations[message.chat.id] = expression

    result = safe_calc(expression)

    if not result.startswith("Ошибка"):
        if save_calculation(message.chat.id, expression, result):
            log_action(message.chat.id, f"Вычисление: {expression} = {result}")

    bot.send_message(message.chat.id,
                     f"Результат: {result}",
                     reply_markup=calcmarkup)


def handle_calculator_operator(message):
    """Добавление оператора"""
    user_calculations[message.chat.id] += f" {message.text} "
    bot.send_message(message.chat.id,
                     f"Текущее: {user_calculations[message.chat.id]}",
                     reply_markup=calcmarkup)


def handle_calculator_digit(message):
    """Добавление цифры"""
    user_calculations[message.chat.id] += message.text
    bot.send_message(message.chat.id,
                     f"Текущее: {user_calculations[message.chat.id]}",
                     reply_markup=calcmarkup)


def handle_calculator_special(message):
    """Добавление спецоператора (^, !, %)"""
    user_calculations[message.chat.id] += message.text
    bot.send_message(message.chat.id,
                     f"Текущее: {user_calculations[message.chat.id]}",
                     reply_markup=calcmarkup)


def handle_calculator_sqrt(message):
    """Добавление квадратного корня"""
    user_calculations[message.chat.id] += "√("
    bot.send_message(message.chat.id,
                     "Пример: √(9)",
                     reply_markup=calcmarkup)