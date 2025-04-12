from telebot import types

# ==================== КЛАВИАТУРЫ ====================
# Главное меню
markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
markup.add(
    types.KeyboardButton("👋 Привет"),
    types.KeyboardButton("❓ Помощь")
)

# Меню приветствия
hellokeys = types.ReplyKeyboardMarkup(resize_keyboard=True)
hellokeys.add(
    types.KeyboardButton("Обо мне ❓"),
    types.KeyboardButton("⚙️ Меню")
)

# Основное меню
menubot = types.ReplyKeyboardMarkup(resize_keyboard=True)
menubot.add(
    types.KeyboardButton("➗ Калькулятор"),
    types.KeyboardButton("🔒 Пароли")
)

# Клавиатура калькулятора
calcmarkup = types.ReplyKeyboardMarkup(resize_keyboard=True)
calcmarkup.row("1", "2", "3", "/", "√(")
calcmarkup.row("4", "5", "6", "*", "^")
calcmarkup.row("7", "8", "9", "+", "!")
calcmarkup.row("0", ".", "res", "-", "%")
calcmarkup.row("🔙 В меню", "Стереть", "История 📜", "Повторить ♻")

# Пароли
password_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
password_markup.add(
    types.KeyboardButton("🔑 Установить мастер-пароль"),
    types.KeyboardButton("➕ Добавить пароль"),
    types.KeyboardButton("📂 Мои пароли"),
    types.KeyboardButton("🔙 Назад")
)