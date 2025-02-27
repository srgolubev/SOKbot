import sys
from pathlib import Path
import json
import os

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.append(str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException, Request, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
import uvicorn
from bot.command_processor import CommandProcessor

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Инициализация FastAPI приложения
app = FastAPI(
    title="Project Sheet Bot API",
    description="API для создания проектных листов в Google Sheets",
    version="1.0.0"
)

# Модель данных для входящего webhook-запроса
class WebhookRequest(BaseModel):
    message: str

# Модель данных для ответа
class WebhookResponse(BaseModel):
    status: str
    message: str

# Инициализация обработчика команд
command_processor = None

# Получение секретного токена из переменных окружения
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

@app.on_event("startup")
async def startup_event():
    """
    Инициализация необходимых компонентов при запуске приложения
    """
    global command_processor
    try:
        logger.info("Начало инициализации приложения")
        command_processor = CommandProcessor()
        logger.info("CommandProcessor успешно инициализирован")
    except Exception as e:
        logger.error(f"Ошибка при инициализации приложения: {str(e)}")
        raise

# Функция для проверки секретного токена
async def verify_telegram_token(x_telegram_bot_api_secret_token: str = Header(None)):
    """
    Проверяет секретный токен от Telegram.
    
    Args:
        x_telegram_bot_api_secret_token: Секретный токен из заголовка запроса
        
    Raises:
        HTTPException: Если токен недействителен
    """
    if WEBHOOK_SECRET and x_telegram_bot_api_secret_token != WEBHOOK_SECRET:
        logger.warning(f"Получен запрос с неверным секретным токеном: {x_telegram_bot_api_secret_token}")
        raise HTTPException(status_code=403, detail="Неверный секретный токен")
    return True

@app.post("/webhook", response_model=WebhookResponse)
async def webhook_handler(request: WebhookRequest, verified: bool = Depends(verify_telegram_token)) -> WebhookResponse:
    """
    Обработчик webhook-запросов.
    
    Args:
        request: Объект WebhookRequest с полем message
        verified: Результат проверки секретного токена
        
    Returns:
        WebhookResponse: Объект с результатом обработки
        
    Raises:
        HTTPException: В случае ошибки обработки запроса
    """
    try:
        logger.info("Начало обработки webhook-запроса")
        logger.debug(f"Получено сообщение: {request.message}")
        
        if command_processor is None:
            error_msg = "CommandProcessor не инициализирован"
            logger.error(error_msg)
            raise HTTPException(
                status_code=500,
                detail=error_msg
            )
        
        # Обработка команды
        logger.info("Передача сообщения в CommandProcessor")
        result = command_processor.process_command(request.message)
        
        logger.info("Запрос успешно обработан")
        logger.debug(f"Результат обработки: {result}")
        
        return WebhookResponse(
            status="success",
            message=result
        )
        
    except Exception as e:
        error_msg = f"Ошибка при обработке webhook-запроса: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@app.post("/webhook/telegram")
async def telegram_webhook_handler(request: Request, verified: bool = Depends(verify_telegram_token)):
    """
    Обработчик webhook-запросов от Telegram.
    
    Args:
        request: Объект Request с данными от Telegram
        verified: Результат проверки секретного токена
        
    Returns:
        dict: Пустой ответ для Telegram
    """
    try:
        logger.info("Начало обработки webhook-запроса от Telegram")
        
        # Получаем данные запроса
        data = await request.json()
        logger.debug(f"Получены данные от Telegram: {data}")
        
        # Проверяем наличие сообщения
        if "message" in data and "text" in data["message"]:
            message_text = data["message"]["text"]
            user_id = data["message"]["from"]["id"]
            username = data["message"]["from"].get("username", "unknown")
            
            logger.info(f"Получено сообщение от пользователя {username} (ID: {user_id}): {message_text}")
            
            if command_processor is None:
                error_msg = "CommandProcessor не инициализирован"
                logger.error(error_msg)
                return {"ok": True}
            
            # Обработка команды
            logger.info("Передача сообщения в CommandProcessor")
            result = command_processor.process_command(message_text)
            
            logger.info("Запрос успешно обработан")
            logger.debug(f"Результат обработки: {result}")
            
            # Здесь можно добавить код для отправки ответа пользователю через Telegram API
            
        return {"ok": True}
        
    except Exception as e:
        error_msg = f"Ошибка при обработке webhook-запроса от Telegram: {str(e)}"
        logger.error(error_msg)
        # Возвращаем успешный ответ Telegram, чтобы избежать повторных запросов
        return {"ok": True}

@app.get("/health")
async def health_check():
    """
    Эндпоинт для проверки работоспособности сервиса
    """
    logger.debug("Получен запрос на проверку здоровья сервиса")
    return {"status": "healthy"}

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware для логирования всех HTTP-запросов
    """
    logger.info(f"Входящий {request.method} запрос на {request.url}")
    
    # Логируем тело запроса для POST-запросов
    if request.method == "POST":
        try:
            body = await request.body()
            if body:
                body_str = body.decode()
                logger.debug(f"Тело запроса: {body_str}")
        except Exception as e:
            logger.error(f"Ошибка при чтении тела запроса: {str(e)}")
    
    response = await call_next(request)
    logger.info(f"Отправлен ответ со статусом {response.status_code}")
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Глобальный обработчик исключений
    """
    error_msg = f"Необработанная ошибка: {str(exc)}"
    logger.error(error_msg)
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": error_msg}
    )

if __name__ == "__main__":
    # Запуск сервера
    logger.info("Запуск сервера FastAPI")
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Автоматическая перезагрузка при изменении кода
    )
