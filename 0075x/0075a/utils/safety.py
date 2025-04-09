import math


def safe_calc(expression: str) -> str:
    """Безопасное вычисление математических выражений."""
    try:
        allowed_chars = set('0123456789.+-*/()^√!% ')
        if not all(c in allowed_chars for c in expression):
            return "Ошибка: недопустимые символы"

        # Замена √ на math.sqrt
        expr = expression.replace('√(', 'math.sqrt(')
        result = eval(expr, {'__builtins__': None, 'math': math})
        return str(round(result, 5))
    except Exception as e:
        return f"Ошибка: {str(e)}"