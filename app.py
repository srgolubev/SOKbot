import sys
from pathlib import Path
import json
import os
from typing import Optional

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.append(str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException, Request, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
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

# Модель данных для сообщения Telegram
#from pydantic import Field

class TelegramUser(BaseModel):
    id: int
    is_bot: bool
    first_name: str
    username: Optional[str] = None

class TelegramMessage(BaseModel):
    message_id: int
    from_user: TelegramUser = Field(..., alias="from")  # <-- Исправлено
    chat: dict
    date: int
    text: Optional[str] = None

# Модель данных для входящего webhook-запроса от Telegram
class TelegramUpdate(BaseModel):
    update_id: int
    message: Optional[TelegramMessage] = None
    my_chat_member: Optional[dict] = None
    callback_query: Optional[dict] = None
    edited_message: Optional[dict] = None
    channel_post: Optional[dict] = None
    edited_channel_post: Optional[dict] = None
    inline_query: Optional[dict] = None
    chosen_inline_result: Optional[dict] = None
    poll: Optional[dict] = None
    poll_answer: Optional[dict] = None

    class Config:
        allow_extra = True  # Разрешаем дополнительные поля

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
        await command_processor.initialize()
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
        
        # Логируем заголовки
        headers = dict(request.headers)
        logger.info(f"Заголовки запроса: {json.dumps(headers, indent=2)}")
        
        # Получаем тело запроса как байты и декодируем
        body_bytes = await request.body()
        body_str = body_bytes.decode()
        logger.info(f"Тело запроса (сырое): {body_str}")
        
        try:
            body = json.loads(body_str)
            logger.info(f"Тело запроса (JSON): {json.dumps(body, indent=2)}")
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка декодирования JSON: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid JSON")
        
        # Проверяем структуру данных
        if not isinstance(body, dict):
            logger.error(f"Тело запроса не является словарем: {type(body)}")
            raise HTTPException(status_code=400, detail="Request body must be a JSON object")
            
        if 'update_id' not in body:
            logger.error(f"Отсутствует обязательное поле update_id в запросе: {body.keys()}")
            raise HTTPException(status_code=400, detail="Missing required field: update_id")
            
        # Проверяем наличие хотя бы одного известного типа обновления
        known_update_types = ['message', 'edited_message', 'channel_post', 'edited_channel_post', 
                             'inline_query', 'chosen_inline_result', 'callback_query', 
                             'poll', 'poll_answer', 'my_chat_member', 'chat_member']
        
        has_known_type = any(update_type in body for update_type in known_update_types)
        if not has_known_type:
            logger.error(f"Неизвестный тип обновления: {body.keys()}")
            raise HTTPException(status_code=400, detail="Unknown update type")
            
        try:
            update = TelegramUpdate(**body)
            logger.info("Данные успешно преобразованы в TelegramUpdate")
        except Exception as e:
            logger.error(f"Ошибка создания объекта TelegramUpdate: {str(e)}")
            raise HTTPException(status_code=422, detail=str(e))
        
        if command_processor is None:
            error_msg = "CommandProcessor не инициализирован"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Обработка различных типов обновлений
        if update.message:
            # Обработка обычного сообщения
            await command_processor.process_message(update.message)
        elif update.my_chat_member:
            # Обработка уведомления о членстве в группе
            logger.info(f"Получено уведомление о членстве в группе: {update.my_chat_member}")
            # Здесь можно добавить логику обработки членства в группе
        elif update.callback_query:
            # Обработка колбэк-запросов от инлайн-кнопок
            logger.info(f"Получен callback_query: {update.callback_query}")
            # Здесь можно добавить логику обработки колбэк-запросов
        else:
            # Логируем другие типы обновлений
            logger.info(f"Получен необрабатываемый тип обновления: {body}")
        
        return {"ok": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обработке webhook-запроса: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

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
