#!/usr/bin/env python
"""
Скрипт для настройки вебхука Telegram.
"""
import os
import sys
import logging
import requests
from dotenv import load_dotenv

# Добавляем родительскую директорию в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Загружаем переменные окружения
load_dotenv()

# Получаем переменные окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/webhook_setup.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def setup_webhook():
    """
    Настраивает вебхук для Telegram бота.
    """
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN не найден в переменных окружения")
        sys.exit(1)
    
    if not WEBHOOK_URL:
        logger.error("WEBHOOK_URL не найден в переменных окружения")
        sys.exit(1)
    
    # Формируем URL для настройки вебхука
    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
    
    # Параметры для настройки вебхука
    params = {
        "url": WEBHOOK_URL + "/telegram",  # Используем специальный эндпоинт для Telegram
        "allowed_updates": ["message", "edited_message", "callback_query"],
    }
    
    # Добавляем секретный токен, если он указан
    if WEBHOOK_SECRET:
        params["secret_token"] = WEBHOOK_SECRET
    
    try:
        # Отправляем запрос на настройку вебхука
        logger.info(f"Настраиваем вебхук на URL: {params['url']}")
        response = requests.post(api_url, json=params)
        response.raise_for_status()
        
        # Проверяем ответ
        result = response.json()
        if result.get("ok"):
            logger.info("Вебхук успешно настроен")
            logger.info(f"Ответ API: {result}")
        else:
            logger.error(f"Ошибка при настройке вебхука: {result}")
            sys.exit(1)
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при отправке запроса: {e}")
        sys.exit(1)

def get_webhook_info():
    """
    Получает информацию о текущем вебхуке.
    """
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN не найден в переменных окружения")
        sys.exit(1)
    
    # Формируем URL для получения информации о вебхуке
    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getWebhookInfo"
    
    try:
        # Отправляем запрос на получение информации о вебхуке
        logger.info("Получаем информацию о текущем вебхуке")
        response = requests.get(api_url)
        response.raise_for_status()
        
        # Проверяем ответ
        result = response.json()
        if result.get("ok"):
            logger.info("Информация о вебхуке получена")
            logger.info(f"Ответ API: {result}")
        else:
            logger.error(f"Ошибка при получении информации о вебхуке: {result}")
            sys.exit(1)
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при отправке запроса: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Создаем директорию для логов, если её нет
    os.makedirs("logs", exist_ok=True)
    
    # Получаем аргументы командной строки
    if len(sys.argv) > 1 and sys.argv[1] == "info":
        get_webhook_info()
    else:
        setup_webhook()
