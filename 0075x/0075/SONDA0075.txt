import sqlite3
import telebot
import threading
from time import sleep
from telebot import types
from datetime import datetime
import math
import os

# Конфигурационные константы
TOKEN = "7463516138:AAE14uskKkSMtI4tIeUWTgNUZjRwbzkI5yc"
ADMIN_ID = 1331203510
DB_BACKUP_FILE = "sonda_backup.db"
BACKUP_INTERVAL_DAYS = 1

# Инициализация бота
bot = telebot.TeleBot(TOKEN)
user_calculations = {}  # Хранение текущих вычислений пользователей

def get_time():
    """Возвращает текущее время в формате HH:MM:SS"""
    return datetime.now().strftime("%H:%M:%S")

def handle_db_errors(func):
    """Декоратор для обработки ошибок базы данных"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except sqlite3.OperationalError as e:
            print(f"[{get_time()}] Ошибка базы данных: {e}")
            log_action(args[0].chat.id if args else 0, f"DB Error: {str(e)}", is_error=True)
            return None
        except sqlite3.IntegrityError as e:
            print(f"[{get_time()}] Ошибка целостности данных: {e}")
            log_action(args[0].chat.id if args else 0, f"Integrity Error: {str(e)}", is_error=True)
            return None
        except sqlite3.Error as e:
            print(f"[{get_time()}] Неизвестная ошибка SQLite: {e}")
            log_action(args[0].chat.id if args else 0, f"Unknown SQL Error: {str(e)}", is_error=True)
            return None
    return wrapper

def notify_admin(error_msg):
    """Отправляет уведомление администратору об ошибке"""
    try:
        bot.send_message(ADMIN_ID, f"🚨 Критическая ошибка:\n{error_msg}")
    except Exception as e:
        print(f"[{get_time()}] Не удалось уведомить администратора: {e}")

def is_admin(user_id):
    """Проверяет, является ли пользователь администратором"""
    return user_id == ADMIN_ID

def log_action(user_id, action, is_error=False):
    """Логирует действие в базу данных"""
    try:
        with sqlite3.connect('sonda_bot.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO logs (user_id, action, timestamp)
            VALUES (?, ?, ?)
            ''', (
                user_id, 
                f"{'🚨 ' if is_error else ''}{action}",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()
    except sqlite3.Error as e:
        print(f"[{get_time()}] Ошибка логирования: {e}")

@handle_db_errors
def backup_db():
    """Создает резервную копию базы данных"""
    try:
        backup_name = f"sonda_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        with open('sonda_bot.db', 'rb') as src, open(backup_name, 'wb') as dst:
            dst.write(src.read())
        log_action(0, f"Создана резервная копия: {backup_name}")
    except Exception as e:
        log_action(0, f"Ошибка резервирования: {str(e)}", is_error=True)
        try:
            backup_name = f"emergency_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            with open('sonda_bot.db', 'rb') as src, open(backup_name, 'wb') as dst:
                dst.write(src.read())
            log_action(0, f"Создана аварийная резервная копия: {backup_name}")
        except Exception as e2:
            log_action(0, f"Критическая ошибка резервирования: {str(e2)}", is_error=True)
            notify_admin(f"Не удалось создать резервную копию: {str(e2)}")

def auto_backup():
    """Фоновая задача для автоматического резервного копирования"""
    while True:
        sleep(BACKUP_INTERVAL_DAYS * 86400)  # Конвертация дней в секунды
        backup_db()

def check_db_file():
    """Проверяет существование файла БД"""
    try:
        if not os.path.exists('sonda_bot.db'):
            print(f"[{get_time()}] Файл БД не найден, будет создан новый")
            init_db()
        else:
            print(f"[{get_time()}] Файл БД найден")
        return True
    except Exception as e:
        print(f"[{get_time()}] Ошибка проверки файла БД: {e}")
        raise

@handle_db_errors
def init_db():
    """Инициализирует базу данных и создает необходимые таблицы"""
    try:
        with sqlite3.connect('sonda_bot.db') as conn:
            cursor = conn.cursor()
        
            # Основные таблицы
            cursor.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                registration_date TEXT
            );
            
            CREATE TABLE IF NOT EXISTS logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT,
                timestamp TEXT
            );
            
            CREATE TABLE IF NOT EXISTS calculations (
                calc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                expression TEXT,
                result TEXT,
                timestamp TEXT
            );
            ''')
            
            # Оптимизации
            cursor.execute('PRAGMA journal_mode=WAL')
            cursor.executescript('''
            CREATE INDEX IF NOT EXISTS idx_logs_user ON logs(user_id);
            CREATE INDEX IF NOT EXISTS idx_calc_user ON calculations(user_id);
            CREATE INDEX IF NOT EXISTS idx_logs_time ON logs(timestamp);
            ''')
            
            # Очистка старых данных
            cursor.execute("DELETE FROM logs WHERE timestamp < datetime('now', '-30 days')")
            
            print(f"[{get_time()}] Инициализация БД завершена")
            conn.commit()
        
        backup_db()
    except Exception as e:
        print(f"[{get_time()}] Критическая ошибка инициализации БД: {e}")
        raise

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
        if '__' in expression or any(op*2 in expression for op in '+-*/^'):
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
                if i == 0 or not expr[i-1].isdigit():
                    return "Не верный ввод. Пример 10!"
                # Находим начало числа
                j = i-1
                while j >= 0 and expr[j].isdigit():
                    j -= 1
                number = expr[j+1:i]
                if not number:
                    return "Ошибка: факториал только для чисел"
                # Заменяем число! на math.factorial(number)
                replacement = f"math.factorial({number})"
                expr = expr[:j+1] + replacement + expr[i+1:]
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

# Инициализация базы данных
init_db()

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

# ==================== ОБРАБОТЧИКИ КОМАНД ====================
@handle_db_errors
@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Обработчик команды /start"""
    try:
        with sqlite3.connect('sonda_bot.db') as conn:
            cursor = conn.cursor()
            # Регистрация нового пользователя
            cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (message.chat.id,))
            if not cursor.fetchone():
                cursor.execute('''
                INSERT INTO users (user_id, username, first_name, last_name, registration_date)
                VALUES (?, ?, ?, ?, ?)
                ''', (
                    message.chat.id,
                    message.from_user.username,
                    message.from_user.first_name,
                    message.from_user.last_name,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

            # Логирование запуска
            cursor.execute('''
            INSERT INTO logs (user_id, action, timestamp)
            VALUES (?, ?, ?)
            ''', (message.chat.id, "start", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()

        bot.send_message(
            message.chat.id,
            "Успешный старт бота.\nГруппа тестировщиков - https://t.me/sondatest",
            reply_markup=markup
        )
        print(f"[{get_time()}] Бот запущен пользователем {message.chat.id}")
    except Exception as e:
        bot.reply_to(message, "⚠ Произошла ошибка при регистрации. Пожалуйста, попробуйте позже.")
        log_action(message.chat.id, f"Ошибка при регистрации: {str(e)}", is_error=True)

@bot.message_handler(commands=['mylogs'])  # Логи для пользователей + Защита
def show_my_logs(message):
    """Показывает логи текущего пользователя"""
    try:
        with sqlite3.connect('sonda_bot.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
            SELECT action, timestamp FROM logs 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 10
            ''', (message.chat.id,))

            logs = cursor.fetchall()

        if not logs:
            bot.reply_to(message, "📭 Ваша история действий пуста")
            return

        response = "📖 Ваши последние 10 действий:\n\n"
        for log in logs:
            response += f"• {log['timestamp']}: {log['action']}\n"

        bot.reply_to(message, response)
        log_action(message.chat.id, "Запрошена история действий")

    except Exception as e:
        bot.reply_to(message, f"⚠ Ошибка: {str(e)}")
        log_action(0, f"Ошибка при запросе логов: {str(e)}", is_error=True)

# Обработчик команды /help
@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
    Доступные команды:
    /start - Запустить бота
    /help - Команды
    /infobot - Обновления бота
    /mylogs - 10 ваших последних действий
    /clearmyhistory - Удалить вашу историю"""
    bot.reply_to(message, help_text)

# Обработчик команды /infobot
@bot.message_handler(commands=['infobot'])
def send_infobot(message):
    infobot_text = """
    Версия SONDA 0.0.74
    Канал по новостям и обновлениям - https://t.me/sondachanel"""
    bot.reply_to(message, infobot_text)

@handle_db_errors
@bot.message_handler(commands=['logs'])
def show_logs(message):
    if not is_admin(message.chat.id):
        bot.reply_to(message, "⛔ Доступ запрещен")
        log_action(message.chat.id, "Попытка доступа к логам без прав", is_error=True)
        return

    try:
        with sqlite3.connect('sonda_bot.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT action, timestamp FROM logs 
            ORDER BY log_id DESC LIMIT 10
            ''')
            logs = cursor.fetchall()

        response = "📃 Последние 10 действий:\n\n"
        for action, timestamp in logs:
            response += f"▫ {timestamp}: {action}\n"
        bot.reply_to(message, response)
        log_action(message.chat.id, "Просмотр логов администратором")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
        log_action(ADMIN_ID, f"Ошибка при показе логов: {str(e)}", is_error=True)

@handle_db_errors
@bot.message_handler(commands=['history'])
def show_history(message):
    """Показывает историю вычислений"""
    try:
        with sqlite3.connect('sonda_bot.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT expression, result, timestamp FROM calculations
            WHERE user_id = ? ORDER BY calc_id DESC LIMIT 5
            ''', (message.chat.id,))
            history = cursor.fetchall()

        if not history:
            bot.reply_to(message, "📭 История вычислений пуста")
            return

        response = "📚 Ваши последние 5 вычислений:\n\n"
        for expr, result, time in history:
            response += f"➤ {expr} = {result}\n   ⌚ {time}\n\n"
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, "⚠ Не удалось загрузить историю вычислений. Пожалуйста, попробуйте позже.")
        log_action(message.chat.id, f"Ошибка показа истории: {str(e)}", is_error=True)

@handle_db_errors
@bot.message_handler(commands=['clearmyhistory']) # Удаляет историю вычислений и действий пользователя
def clear_user_history(message):
    try:
        with sqlite3.connect('sonda_bot.db') as conn:
            cursor = conn.cursor()
            # Удаляем историю вычислений
            cursor.execute('DELETE FROM calculations WHERE user_id = ?', (message.chat.id,))
            # Удаляем логи пользователя (кроме команды очистки)
            cursor.execute('DELETE FROM logs WHERE user_id = ? AND action != "Очищена история"', (message.chat.id,))
            # Логируем действие
            cursor.execute('''
            INSERT INTO logs (user_id, action, timestamp)
            VALUES (?, ?, ?)
            ''', (
                message.chat.id,
                "Очищена история",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()
        bot.reply_to(message, "✅ Ваша история вычислений и действий была очищена")
    except Exception as e:
        bot.reply_to(message, f"⚠ Ошибка при очистке истории: {str(e)}")
        log_action(0, f"Ошибка очистки истории: {str(e)}", is_error=True)

# Обработка кнопок
@bot.message_handler(content_types=['text'])
def handle_buttons(message):
    if message.text == "👋 Привет":
        bot.reply_to(message, "Привет, я SONDA - Бот который может очень многое. Пользуйся мной во благо себя.",
                     reply_markup=hellokeys)
        print(f"[{get_time()}] Обработана КНОПКА '👋 Привет'")
        log_action(message.chat.id, "Нажата кнопка '👋 Привет'")
    elif message.text == "❓ Помощь":
        help_text = """
        Доступные команды:
        /start - Запустить бота
        /help - Команды
        /infobot - Обновления бота
        /mylogs - 10 ваших последних действий
        /clearmyhistory - Удалить вашу историю"""
        bot.reply_to(message, help_text)
        print(f"[{get_time()}] Обработана КНОПКА '❓ Помощь', выдан текст КОМАНДЫ help")
        log_action(message.chat.id, "Нажата кнопка '❓ Помощь'")
    elif message.text == "Обо мне ❓":
        obomne_text = """
        SONDA - это бот, а название - совмещение имён Даня и Соня.
        Пока у меня нет никаких возможностей,
        но вскоре они появится и ого-го какие..
        На этом всё. Удачи)"""
        bot.reply_to(message, obomne_text, reply_markup=markup)
        print(f"[{get_time()}] Обработана КНОПКА 'Обо мне ❓'")
        log_action(message.chat.id, "Нажата кнопка 'Обо мне ❓'")
    elif message.text == "⚙️ Меню":
        bot.reply_to(message, "Основной функционал.", reply_markup=menubot)
        print(f"[{get_time()}] Обработана КНОПКА '⚙️ Меню'")
        log_action(message.chat.id, "Нажата кнопка '⚙️ Меню'")
    elif message.text == "➗ Калькулятор":
        user_calculations[message.chat.id] = ""
        bot.send_message(message.chat.id, "Режим калькулятора...", reply_markup=calcmarkup)
        log_action(message.chat.id, "Открыт калькулятор")
    elif message.chat.id in user_calculations:
        if message.text == "🔙 В меню":
            del user_calculations[message.chat.id]
            bot.send_message(message.chat.id, "Главное меню:", reply_markup=markup)
        elif message.text == "История 📜":
            show_history(message)
        elif message.text == "Стереть":
            user_calculations[message.chat.id] = ""
            bot.send_message(message.chat.id, "Калькулятор очищен.\nТекущее: 0", reply_markup=calcmarkup)
        elif message.text == "Повторить ♻":
            last_calc = get_last_calculation(message.chat.id)
            if last_calc:
                user_calculations[message.chat.id] = last_calc['expression']
                bot.send_message(message.chat.id,
                               f"↩ Повтор: {last_calc['expression']}\nТекущее: {last_calc['expression']}",
                               reply_markup=calcmarkup)
            else:
                bot.send_message(message.chat.id,
                               "История вычислений пуста",
                               reply_markup=calcmarkup)
        elif message.text == "res":
            if not user_calculations.get(message.chat.id) or not user_calculations[message.chat.id].strip():
                bot.send_message(message.chat.id, "Введите выражение сначала", reply_markup=calcmarkup)
                return
                
            expression = user_calculations[message.chat.id].strip()
            
            # Автодобавление закрывающей скобки для корня если нужно
            if '√(' in expression and expression.count('(') > expression.count(')'):
                expression += ")"
                user_calculations[message.chat.id] = expression
            
            result = safe_calc(expression)
            
            if not result.startswith("Ошибка"):
                try:
                    log_action(message.chat.id, f"Вычисление: {expression} = {result}")
                    with sqlite3.connect('sonda_bot.db') as conn:
                        cursor = conn.cursor()
                        cursor.execute('''
                        INSERT INTO calculations (user_id, expression, result, timestamp)
                        VALUES (?, ?, ?, ?)
                        ''', (
                            message.chat.id,
                            expression,
                            result,
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ))
                        conn.commit()
                except Exception as e:
                    log_action(message.chat.id, f"Ошибка сохранения вычисления: {str(e)}", is_error=True)
            
            if "Ошибка" in result:
                bot.send_message(message.chat.id, f"Ошибка: {result}", reply_markup=calcmarkup)
            else:
                bot.send_message(
                    message.chat.id,
                    f"Результат: {result}",
                    reply_markup=calcmarkup
                )
        elif message.text in ["+", "-", "*", "/"]:
            user_calculations[message.chat.id] += f" {message.text} "
            bot.send_message(message.chat.id, f"Текущий пример: {user_calculations[message.chat.id]} Вводите дальше.")
        elif message.text.isdigit() or message.text == ".":
            user_calculations[message.chat.id] += message.text
            bot.send_message(message.chat.id, f"Текущий пример: {user_calculations[message.chat.id]} Вводите дальше.")
        elif message.text in ["^", "!", "%"]:
            user_calculations[message.chat.id] += message.text
            bot.send_message(
                message.chat.id,
                f"Текущее: {user_calculations[message.chat.id]}",
                reply_markup=calcmarkup
            )
        elif message.text == "√(":
            user_calculations[message.chat.id] += "√("
            bot.send_message(
                message.chat.id,
                "Пример: √(9) = 3\nНе забудьте закрыть скобку!",
                reply_markup=calcmarkup
            )

# Запускаем бота
if __name__ == "__main__":
    print(f"[{get_time()}] Бот запускается...")
    try:
        check_db_file()
        init_db()
        backup_thread = threading.Thread(target=auto_backup, daemon=True)
        backup_thread.start()
        
        while True:
            try:
                bot.polling(none_stop=True)
            except Exception as e:
                print(f"[{get_time()}] Ошибка в основном цикле: {e}")
                log_action(0, f"Ошибка в основном цикле: {str(e)}", is_error=True)
                sleep(10)
    except KeyboardInterrupt:
        print(f"[{get_time()}] Бот остановлен пользователем")
        log_action(0, "Бот остановлен пользователем")
        try:
            backup_db()
        except:
            pass
    except Exception as e:
        print(f"[{get_time()}] Критическая ошибка: {e}")
        try:
            backup_db()
        except:
            pass
        notify_admin(f"Бот остановлен с ошибкой: {str(e)}")
        raise