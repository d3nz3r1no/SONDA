import telebot

# Конфигурационные константы
TOKEN = "7463516138:AAFpFJO-q-iFX-xU7j6OBpUbrNPiK_DCVVU"
ADMIN_ID = 1331203510
DB_BACKUP_FILE = "sonda_backup.db"
BACKUP_INTERVAL_DAYS = 1

# Инициализация бота
bot = telebot.TeleBot(TOKEN)