import os
from dotenv import load_dotenv

def load_config():
    """
    Загружает конфигурацию из переменных окружения
    
    Returns:
        dict: Словарь с конфигурацией
    """
    load_dotenv()
    
    config = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN"),
        "GOOGLE_SHEETS_ID": os.getenv("GOOGLE_SHEETS_ID"),
        "GOOGLE_CREDENTIALS_FILE": os.path.join("credentials", "credentials.json")
    }
    
    return config
