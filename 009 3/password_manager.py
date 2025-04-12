from datetime import datetime
from db import db
from encryption import *
import bcrypt
from cmd import bot, log_action
import logging
import traceback

logger = logging.getLogger(__name__)

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
        conn.commit()
        if not conn:
            logger.error("Не удалось подключиться к БД")
            return
    except Exception as e:
        logger.error(f"Ошибка в process_set_master: {str(e)}")
        logger.error(f"Ошибка: {str(e)}\n{traceback.format_exc()}")
    finally:
        conn.close()


def process_add_password(message):
    """Добавление пароля"""
    try:
        if ":" not in message.text:
            raise ValueError("Неверный формат")
        service, password = message.text.split(":", 1)
        service = service.strip()
        password = password.strip()

        # Получаем хэш мастер-пароля
        conn = db.get_connection()
        row = conn.execute('SELECT master_key_hash FROM master_keys WHERE user_id = ?', (message.chat.id,)).fetchone()
        if not row:
            bot.reply_to(message, "❌ Сначала установите мастер-пароль!")
            return

        msg = bot.send_message(message.chat.id, "🔑 Введите мастер-пароль для подтверждения:")
        bot.register_next_step_handler(msg, lambda m: _finish_add_password(m, service, password))

        # Генерируем ключ и шифруем
        salt = bcrypt.gensalt()
        key = generate_key(master_password, salt)
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
    except ValueError:
        bot.reply_to(message, "❌ Используйте формат: Сервис:Пароль")

    except Exception as e:
        bot.reply_to(message, f"⚠ Ошибка: {str(e)}")
        logger.error(f"Ошибка: {str(e)}\n{traceback.format_exc()}")

    finally:
        if conn:
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
        logger.error(f"Ошибка: {str(e)}\n{traceback.format_exc()}")
    finally:
        conn.close()


def _finish_add_password(message, service, password_to_encrypt):
    master_password = message.text.strip()
    conn = db.get_connection()
    if not conn:
        bot.reply_to(message, "❌ Ошибка подключения к БД")
        return

    try:
        # Генерация соли и ключа
        salt = bcrypt.gensalt()
        key = generate_key(master_password, salt)
        iv, encrypted = encrypt_password(key, password_to_encrypt)

        # Корректный SQL-запрос с 6 параметрами
        conn.execute('''
            INSERT INTO passwords (
                user_id, 
                service_name, 
                encrypted_password, 
                iv, 
                salt, 
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            message.chat.id,
            service,
            encrypted.hex(),
            iv.hex(),
            salt.hex(),  # Добавлен salt
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()  # Фиксация изменений
        bot.reply_to(message, f"✅ Пароль для {service} сохранен!")

    except Exception as e:
        logger.error(f"Ошибка: {str(e)}", exc_info=True)  # Подробное логирование
        bot.reply_to(message, "⚠ Ошибка сохранения. Проверьте логи.")
    finally:
        if conn:
            conn.close()  # Закрытие соединения

def ask_for_service(message):
    """Запрос названия сервиса"""
    msg = bot.send_message(message.chat.id, "📝 Введите название сервиса:")
    bot.register_next_step_handler(msg, ask_for_master_password)

def ask_for_master_password(message):
    """Запрос мастер-пароля"""
    service_name = message.text.strip()
    msg = bot.send_message(message.chat.id, "🔑 Введите мастер-пароль:")
    bot.register_next_step_handler(msg, lambda m: decrypt_password_handler(m, service_name))

def decrypt_password_handler(message, service_name):
    master_password = message.text.strip()
    conn = db.get_connection()
    try:
        # Получаем данные из БД, включая соль
        row = conn.execute('''
            SELECT encrypted_password, iv, salt 
            FROM passwords 
            WHERE user_id = ? AND service_name = ?
        ''', (message.chat.id, service_name)).fetchone()

        if not row:
            bot.reply_to(message, "❌ Сервис не найден")
            return

        # Используем сохраненную соль
        salt = bytes.fromhex(row['salt'])  # Конвертируем из hex
        iv = bytes.fromhex(row['iv'])
        encrypted_password = bytes.fromhex(row['encrypted_password'])

        # Генерируем ключ
        key = generate_key(master_password, salt)
        decrypted = decrypt_password(key, iv, encrypted_password)

        bot.reply_to(message, f"🔓 Пароль для {service_name}: {decrypted}")
    except Exception as e:
        bot.reply_to(message, f"⚠ Ошибка: {str(e)}")
        logger.error(f"Ошибка: {str(e)}\n{traceback.format_exc()}")
    finally:
        conn.close()

def show_password(message):
    """Просмотр пароля по мастер-паролю"""
    msg = bot.send_message(message.chat.id, "Введите мастер-пароль:")
    bot.register_next_step_handler(msg, lambda m: decrypt_password_handler(m, service_name))

def decrypt_password_handler(message, service_name):
    master_password = message.text
    # Получите из БД iv и encrypted_password
    # Сгенерируйте ключ и расшифруйте
    # Отправьте результат

def process_set_master(message):
    msg = bot.send_message(message.chat.id, "Повторите мастер-пароль:")
    bot.register_next_step_handler(msg, lambda m: confirm_master_password(m, message.text))

def confirm_master_password(message, first_password):
    if message.text != first_password:
        bot.reply_to(message, "❌ Пароли не совпадают")