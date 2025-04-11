from telebot import types


def create_main_keyboard():
    """Создает главную клавиатуру (основное меню)"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("👋 Привет"),
        types.KeyboardButton("❓ Помощь"),
        types.KeyboardButton("⚙️ Меню"),
        types.KeyboardButton("➗ Калькулятор")
    )
    return markup


def create_hello_keyboard():
    """Клавиатура для приветственного сообщения"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("Обо мне ❓"),
        types.KeyboardButton("⚙️ Меню"),
        types.KeyboardButton("🔙 Назад")
    )
    return markup


def create_menu_keyboard():
    """Клавиатура основного меню"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("➗ Калькулятор"),
        types.KeyboardButton("🔒 Пароли"),
        types.KeyboardButton("📊 Статистика"),
        types.KeyboardButton("🔙 Назад")
    )
    return markup


def create_calculator_keyboard():
    """Клавиатура калькулятора (полная версия из 0.0.74)"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    # Первый ряд
    markup.row(
        types.KeyboardButton("1"),
        types.KeyboardButton("2"),
        types.KeyboardButton("3"),
        types.KeyboardButton("/"),
        types.KeyboardButton("√(")
    )

    # Второй ряд
    markup.row(
        types.KeyboardButton("4"),
        types.KeyboardButton("5"),
        types.KeyboardButton("6"),
        types.KeyboardButton("*"),
        types.KeyboardButton("^")
    )

    # Третий ряд
    markup.row(
        types.KeyboardButton("7"),
        types.KeyboardButton("8"),
        types.KeyboardButton("9"),
        types.KeyboardButton("+"),
        types.KeyboardButton("!")
    )

    # Четвертый ряд
    markup.row(
        types.KeyboardButton("0"),
        types.KeyboardButton("."),
        types.KeyboardButton("res"),
        types.KeyboardButton("-"),
        types.KeyboardButton("%")
    )

    # Пятый ряд (управление)
    markup.row(
        types.KeyboardButton("🔙 В меню"),
        types.KeyboardButton("Стереть"),
        types.KeyboardButton("История 📜"),
        types.KeyboardButton("Повторить ♻")
    )

    return markup


def create_passwords_keyboard():
    """Клавиатура менеджера паролей"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🔐 Добавить пароль"),
        types.KeyboardButton("📋 Список паролей"),
        types.KeyboardButton("✏️ Изменить пароль"),
        types.KeyboardButton("❌ Удалить пароль"),
        types.KeyboardButton("🔙 В меню")
    )
    return markup


def create_admin_keyboard():
    """Клавиатура администратора (если ADMIN_ID)"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("📊 Статистика"),
        types.KeyboardButton("📜 Логи"),
        types.KeyboardButton("🛡️ Безопасность"),
        types.KeyboardButton("🔙 В меню")
    )
    return markup


def create_back_only_keyboard():
    """Минимальная клавиатура с кнопкой Назад"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🔙 Назад"))
    return markup


# Глобальные экземпляры клавиатур для быстрого доступа
main_markup = create_main_keyboard()
hello_markup = create_hello_keyboard()
menu_markup = create_menu_keyboard()
calc_markup = create_calculator_keyboard()
pass_markup = create_passwords_keyboard()
admin_markup = create_admin_keyboard()
back_markup = create_back_only_keyboard()