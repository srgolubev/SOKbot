import os
import logging
import json
from typing import Dict, Optional
import requests
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('telegram_webhook.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Получение конфигурации из переменных окружения
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # Например: https://your-domain.com/webhook
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', '')  # Секретный токен для дополнительной защиты

if not TELEGRAM_TOKEN or not WEBHOOK_URL:
    raise ValueError("Не установлены TELEGRAM_TOKEN или WEBHOOK_URL в переменных окружения")

# Инициализация FastAPI приложения
app = FastAPI(
    title="Telegram Webhook API",
    description="API для обработки вебхуков от Telegram Bot API",
    version="1.0.0"
)

class TelegramUpdate(BaseModel):
    """Модель данных для входящих обновлений от Telegram"""
    update_id: int
    message: Optional[Dict] = None
    edited_message: Optional[Dict] = None
    channel_post: Optional[Dict] = None
    edited_channel_post: Optional[Dict] = None
    callback_query: Optional[Dict] = None

def setup_webhook() -> bool:
    """
    Настраивает вебхук для Telegram бота
    
    Returns:
        bool: True если вебхук успешно установлен, False в случае ошибки
    """
    try:
        # Формируем URL для установки вебхука
        api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
        
        # Подготавливаем параметры запроса
        params = {
            "url": f"{WEBHOOK_URL}/webhook",
            "secret_token": WEBHOOK_SECRET if WEBHOOK_SECRET else None,
            "allowed_updates": ["message", "edited_message", "callback_query"]
        }
        
        # Удаляем None значения из параметров
        params = {k: v for k, v in params.items() if v is not None}
        
        logger.info(f"Отправка запроса на установку вебхука: {api_url}")
        logger.debug(f"Параметры запроса: {json.dumps(params, ensure_ascii=False)}")
        
        # Отправляем запрос к Telegram API
        response = requests.post(api_url, json=params)
        response.raise_for_status()
        
        result = response.json()
        if result.get("ok"):
            logger.info("Вебхук успешно установлен")
            return True
        else:
            logger.error(f"Ошибка при установке вебхука: {result.get('description')}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка сети при установке вебхука: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка при установке вебхука: {str(e)}")
        return False

@app.on_event("startup")
async def startup_event():
    """Выполняется при запуске приложения"""
    logger.info("Инициализация приложения")
    if not setup_webhook():
        raise RuntimeError("Не удалось установить вебхук")

@app.post("/webhook")
async def telegram_webhook(update: TelegramUpdate, request: Request):
    """
    Обработчик входящих обновлений от Telegram
    
    Args:
        update: Объект обновления от Telegram
        request: Объект запроса FastAPI
        
    Returns:
        dict: Пустой словарь (Telegram ожидает код 200 и пустой ответ)
        
    Raises:
        HTTPException: В случае ошибки обработки запроса
    """
    try:
        # Проверяем секретный токен, если он установлен
        if WEBHOOK_SECRET:
            secret_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
            if not secret_header or secret_header != WEBHOOK_SECRET:
                logger.warning("Получен запрос с неверным секретным токеном")
                raise HTTPException(status_code=403, detail="Неверный секретный токен")
        
        # Логируем полученное обновление
        logger.info(f"Получено обновление: {update.update_id}")
        logger.debug(f"Данные обновления: {json.dumps(update.dict(), ensure_ascii=False)}")
        
        # Обрабатываем сообщение
        if update.message and update.message.get("text"):
            chat_id = update.message["chat"]["id"]
            text = update.message["text"]
            logger.info(f"Получено сообщение от {chat_id}: {text}")
            
            # Здесь будет ваша логика обработки сообщений
            # Например, вызов CommandProcessor
            
        return {}
        
    except Exception as e:
        error_msg = f"Ошибка при обработке вебхука: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/webhook/info")
async def webhook_info():
    """
    Получает информацию о текущих настройках вебхука
    """
    try:
        api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getWebhookInfo"
        response = requests.get(api_url)
        response.raise_for_status()
        return response.json()
        
    except Exception as e:
        error_msg = f"Ошибка при получении информации о вебхуке: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

if __name__ == "__main__":
    import uvicorn
    
    # Запуск сервера
    logger.info("Запуск сервера FastAPI")
    uvicorn.run(
        "telegram_webhook:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
