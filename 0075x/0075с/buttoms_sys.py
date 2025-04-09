from calc_sys import *
from cmd import *

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