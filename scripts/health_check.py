#!/usr/bin/env python
"""
Скрипт для проверки здоровья системы.
"""
import os
import sys
import time
import logging
import requests
from dotenv import load_dotenv

# Добавляем родительскую директорию в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Загружаем переменные окружения
load_dotenv()

# Получаем переменные окружения
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://srgolubev.ru/webhook")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/health_check.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_domain_server():
    """
    Проверяет доступность сервера с доменом.
    """
    domain_server_ip = "95.163.234.54"
    logger.info(f"Проверка сервера с доменом ({domain_server_ip})...")
    
    try:
        # Проверяем доступность домена
        domain = "srgolubev.ru"
        response = requests.get(f"https://{domain}", timeout=5)
        logger.info(f"Домен {domain} доступен, статус: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при проверке домена: {e}")
        return False

def check_bot_server():
    """
    Проверяет доступность сервера с ботом.
    """
    bot_server_ip = "212.224.118.58"
    logger.info(f"Проверка сервера с ботом ({bot_server_ip})...")
    
    try:
        # Проверяем доступность эндпоинта /health
        health_url = f"{WEBHOOK_URL.rstrip('/')}/health"
        response = requests.get(health_url, timeout=5)
        logger.info(f"Эндпоинт /health доступен, статус: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при проверке эндпоинта /health: {e}")
        return False

def check_telegram_webhook():
    """
    Проверяет настройку вебхука Telegram.
    """
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN не найден в переменных окружения")
        return False
    
    logger.info("Проверка настройки вебхука Telegram...")
    
    try:
        # Получаем информацию о вебхуке
        api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getWebhookInfo"
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()
        
        # Проверяем ответ
        result = response.json()
        if result.get("ok"):
            webhook_info = result.get("result", {})
            webhook_url = webhook_info.get("url", "")
            
            if webhook_url:
                logger.info(f"Вебхук настроен на URL: {webhook_url}")
                
                # Проверяем, соответствует ли URL ожидаемому
                expected_url = f"{WEBHOOK_URL.rstrip('/')}/telegram"
                if webhook_url == expected_url:
                    logger.info("URL вебхука соответствует ожидаемому")
                else:
                    logger.warning(f"URL вебхука не соответствует ожидаемому: {expected_url}")
                
                # Проверяем, есть ли ошибки
                if webhook_info.get("last_error_date"):
                    last_error_message = webhook_info.get("last_error_message", "")
                    logger.error(f"Последняя ошибка вебхука: {last_error_message}")
                    return False
                
                return True
            else:
                logger.warning("Вебхук не настроен")
                return False
        else:
            logger.error(f"Ошибка при получении информации о вебхуке: {result}")
            return False
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при отправке запроса: {e}")
        return False

def run_health_check():
    """
    Запускает проверку здоровья системы.
    """
    logger.info("Запуск проверки здоровья системы...")
    
    # Проверяем сервер с доменом
    domain_server_ok = check_domain_server()
    
    # Проверяем сервер с ботом
    bot_server_ok = check_bot_server()
    
    # Проверяем настройку вебхука Telegram
    webhook_ok = check_telegram_webhook()
    
    # Выводим общий статус
    logger.info("Результаты проверки здоровья системы:")
    logger.info(f"Сервер с доменом: {'OK' if domain_server_ok else 'ОШИБКА'}")
    logger.info(f"Сервер с ботом: {'OK' if bot_server_ok else 'ОШИБКА'}")
    logger.info(f"Вебхук Telegram: {'OK' if webhook_ok else 'ОШИБКА'}")
    
    # Общий статус
    overall_status = domain_server_ok and bot_server_ok and webhook_ok
    logger.info(f"Общий статус: {'OK' if overall_status else 'ОШИБКА'}")
    
    return overall_status

if __name__ == "__main__":
    # Создаем директорию для логов, если её нет
    os.makedirs("logs", exist_ok=True)
    
    # Запускаем проверку здоровья
    success = run_health_check()
    
    # Выходим с соответствующим кодом
    sys.exit(0 if success else 1)
