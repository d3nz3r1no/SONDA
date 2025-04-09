import telebot

# Конфигурационные константы
TOKEN = "7463516138:AAE14uskKkSMtI4tIeUWTgNUZjRwbzkI5yc"
ADMIN_ID = 1331203510
DB_BACKUP_FILE = "sonda_backup.db"
BACKUP_INTERVAL_DAYS = 1
bot = telebot.TeleBot(TOKEN)
user_calculations = {}  # Хранение текущих вычислений пользователей