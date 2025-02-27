import sys
from pathlib import Path
import json

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.append(str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException, Request
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

@app.post("/webhook", response_model=WebhookResponse)
async def webhook_handler(request: WebhookRequest) -> WebhookResponse:
    """
    Обработчик webhook-запросов.
    
    Args:
        request: Объект WebhookRequest с полем message
        
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

@app.get("/health")
async def health_check():
    """
    Эндпоинт для проверки работоспособности сервиса
    """
    logger.debug("Получен запрос на проверку здоровья сервиса")
    return {"status": "healthy"}

if __name__ == "__main__":
    # Запуск сервера
    logger.info("Запуск сервера FastAPI")
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Автоматическая перезагрузка при изменении кода
    )
