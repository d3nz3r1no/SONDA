# Основные настройки бота
TOKEN = "7463516138:AAE14uskKkSMtI4tIeUWTgNUZjRwbzkI5yc"  # Токен бота Telegram
ADMIN_ID = 1331203510  # ID администратора бота

# Настройки базы данных
DB_NAME = "sonda_bot.db"  # Имя файла базы данных
DB_BACKUP_FILE = "sonda_backup.db"  # Шаблон имени для резервных копий
BACKUP_INTERVAL_DAYS = 1  # Интервал создания резервных копий (в днях)

# Настройки безопасности
MAX_EXPRESSION_LENGTH = 50  # Максимальная длина математического выражения
MAX_INPUT_LENGTH = 100  # Максимальная длина пользовательского ввода
PASSWORD_MIN_LENGTH = 8  # Минимальная длина пароля

# Настройки логирования
LOG_RETENTION_DAYS = 30  # Хранение логов (в днях)
MAX_LOG_ENTRIES = 1000  # Максимальное количество записей в логе

# Ссылки и контакты
TESTERS_GROUP = "https://t.me/sondatest"  # Группа тестировщиков
NEWS_CHANNEL = "https://t.me/sondachanel"  # Канал новостей
SUPPORT_EMAIL = "sonda.bot.support@gmail.com"  # Почта поддержки

# Текстовые константы
BOT_VERSION = "0.0.74"  # Версия бота
BOT_NAME = "SONDA"  # Имя бота
BOT_DESCRIPTION = "Бот-калькулятор с дополнительными функциями"  # Описание

# Настройки отображения
DECIMAL_PLACES = 5  # Количество знаков после запятой
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"  # Формат даты и времени