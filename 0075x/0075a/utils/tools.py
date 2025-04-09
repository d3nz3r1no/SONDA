from datetime import datetime

def get_time():
    """Возвращает время в формате HH:MM:SS."""
    return datetime.now().strftime("%H:%M:%S")