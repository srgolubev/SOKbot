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

# Модель данных для входящего webhook-запроса от Telegram
class TelegramUpdate(BaseModel):
    update_id: int
    message: dict

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

@app.post("/webhook")
async def telegram_webhook_handler(request: Request, verified: bool = Depends(verify_telegram_token)):
    """
    Обработчик webhook-запросов от Telegram.
    """
    try:
        logger.info("Начало обработки webhook-запроса от Telegram")
        
        # Получаем и логируем сырые данные
        body = await request.json()
        logger.info(f"Получены данные от Telegram: {json.dumps(body, indent=2)}")
        
        # Проверяем структуру данных
        if not isinstance(body, dict) or 'update_id' not in body or 'message' not in body:
            logger.error(f"Некорректная структура данных: {body}")
            return {}
            
        update = TelegramUpdate(**body)
        
        if command_processor is None:
            error_msg = "CommandProcessor не инициализирован"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Обработка сообщения
        await command_processor.process_message(update.message)
        
        return {}
        
    except Exception as e:
        logger.error(f"Ошибка при обработке webhook-запроса: {str(e)}")
        # Возвращаем пустой ответ, чтобы Telegram не пытался переотправить сообщение
        return {}

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
