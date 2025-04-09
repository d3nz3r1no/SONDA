import math
from dberrorslog import *

def safe_calc(expression):
    """Безопасное вычисление с поддержкой новых операций"""
    try:
        # Проверка на простое число
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

        # Разрешенные символы (добавлены ^, √, !, %)
        allowed_chars = set('0123456789.+-*/()^√!% ')
        if not all(c in allowed_chars for c in expression):
            return "Недопустимые символы"

        # Замена операторов на Python-синтаксис
        expr = (expression
                .replace('^', '**')
                .replace('√(', 'math.sqrt(')
                .replace('%', '/100'))

        # Улучшенная обработка факториала
        i = 0
        while i < len(expr):
            if expr[i] == '!':
                if i == 0 or not expr[i - 1].isdigit():
                    return "Не верный ввод. Пример 10!"
                # Находим начало числа
                j = i - 1
                while j >= 0 and expr[j].isdigit():
                    j -= 1
                number = expr[j + 1:i]
                if not number:
                    return "Ошибка: факториал только для чисел"
                # Заменяем число! на math.factorial(number)
                replacement = f"math.factorial({number})"
                expr = expr[:j + 1] + replacement + expr[i + 1:]
                i = j + len(replacement)
            else:
                i += 1

        # Вычисление с ограниченным globals (для безопасности)
        result = eval(expr, {'__builtins__': None, 'math': math})
        return str(round(result, 5))  # Округление до 5 знаков

    except ZeroDivisionError:
        return "Деление на ноль"
    except ValueError:
        return "Недопустимое значение (например, √-1)"
    except Exception as e:
        return f"Ошибка в выражении: {str(e)}"


@handle_db_errors
def get_last_calculation(user_id):
    """Возвращает последнее вычисление пользователя"""
    try:
        with sqlite3.connect('sonda_bot.db') as conn:
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
        log_action(user_id, f"Ошибка получения вычисления: {str(e)}", is_error=True)
        return None