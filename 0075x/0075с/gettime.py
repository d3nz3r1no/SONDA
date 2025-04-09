from datetime import datetime

# Выводит время, например для логов
def get_time():
    return datetime.now().strftime("%H:%M:%S")