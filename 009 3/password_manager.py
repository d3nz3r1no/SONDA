from telebot import types
from db import db
from encryption import *
import bcrypt
from cmd import bot, log_action


def handle_password_buttons(message):
    """Обработчик кнопок меню паролей"""
    if message.text == "🔑 Установить мастер-пароль":
        msg = bot.send_message(message.chat.id, "Введите новый мастер-пароль:")
        bot.register_next_step_handler(msg, process_set_master)
    elif message.text == "➕ Добавить пароль":
        msg = bot.send_message(message.chat.id, "Введите сервис и пароль в формате: Сервис:Пароль")
        bot.register_next_step_handler(msg, process_add_password)
    elif message.text == "📂 Мои пароли":
        show_passwords_list(message)


def process_set_master(message):
    """Установка мастер-пароля"""
    master_password = message.text.strip()
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(master_password.encode(), salt)

    conn = db.get_connection()
    try:
        conn.execute('''
            INSERT OR REPLACE INTO master_keys (user_id, master_key_hash)
            VALUES (?, ?)
        ''', (message.chat.id, hashed.decode()))
        conn.commit()
        bot.reply_to(message, "✅ Мастер-пароль установлен")
        log_action(message.chat.id, "Установлен мастер-пароль")
    except Exception as e:
        bot.reply_to(message, "⚠ Ошибка: " + str(e))
    finally:
        conn.close()


def process_add_password(message):
    """Добавление пароля"""
    try:
        service, password = message.text.split(":", 1)
        service = service.strip()
        password = password.strip()

        # Получаем хэш мастер-пароля
        conn = db.get_connection()
        row = conn.execute('SELECT master_key_hash FROM master_keys WHERE user_id = ?', (message.chat.id,)).fetchone()
        if not row:
            bot.reply_to(message, "❌ Сначала установите мастер-пароль!")
            return

        # Генерируем ключ и шифруем
        salt = bcrypt.gensalt()
        key = generate_key(row[0], salt)
        iv, encrypted = encrypt_password(key, password)

        # Сохраняем в БД
        conn.execute('''
            INSERT INTO passwords (user_id, service_name, encrypted_password, iv, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            message.chat.id,
            service,
            encrypted.hex(),
            iv.hex(),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        bot.reply_to(message, f"✅ Пароль для {service} сохранен!")
        log_action(message.chat.id, f"Добавлен пароль для {service}")

    except Exception as e:
        bot.reply_to(message, f"⚠ Ошибка: {str(e)}")
    finally:
        conn.close()


def show_passwords_list(message):
    """Показать список сервисов"""
    conn = db.get_connection()
    try:
        services = conn.execute('''
            SELECT service_name, created_at FROM passwords 
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (message.chat.id,)).fetchall()

        if not services:
            bot.reply_to(message, "📭 У вас нет сохраненных паролей")
            return

        response = "🔐 Ваши сервисы:\n\n" + "\n".join(
            f"• {service[0]} (добавлен {service[1]})"
            for service in services
        )
        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"⚠ Ошибка: {str(e)}")
    finally:
        conn.close()

