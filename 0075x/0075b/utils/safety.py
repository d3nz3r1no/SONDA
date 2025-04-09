import math
import re
from utils.logger import log_action
from database.decorators import handle_db_errors, admin_required


def safe_calc(expression: str) -> str:
    """
    Безопасное вычисление математических выражений
    Полная оригинальная реализация из SONDA 0.0.74

    :param expression: Строка с математическим выражением
    :return: Результат вычисления или сообщение об ошибке
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
                    return "Неверный ввод. Пример: 10!"
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


def validate_password(password: str) -> bool:
    """
    Проверка сложности пароля
    Реализация из оригинального кода 0.0.74

    :param password: Пароль для проверки
    :return: True если пароль надежный
    """
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    return True


def sanitize_input(text: str, max_length: int = 100) -> str:
    """
    Очистка пользовательского ввода
    Реализация из оригинального кода 0.0.74

    :param text: Входной текст
    :param max_length: Максимальная допустимая длина
    :return: Очищенный текст
    """
    if not text:
        return ""

    # Удаляем опасные символы
    cleaned = re.sub(r'[;\\\'"<>]', '', text.strip())

    # Обрезаем до максимальной длины
    return cleaned[:max_length]


def is_admin(user_id: int) -> bool:
    """
    Проверка прав администратора
    Реализация из оригинального кода 0.0.74

    :param user_id: ID пользователя для проверки
    :return: True если пользователь администратор
    """
    from config import ADMIN_ID
    return user_id == ADMIN_ID