import os
import json
import logging
from typing import Dict, List, Tuple, Optional
from openai import OpenAI
from dotenv import load_dotenv
from .sheets_api import GoogleSheetsAPI
import telegram

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('command_processor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CommandProcessor:
    def __init__(self):
        """
        Инициализация процессора команд.
        Загружает переменные окружения и инициализирует клиенты API.
        """
        try:
            logger.info("Начало инициализации CommandProcessor")
            
            # Загружаем переменные окружения
            load_dotenv()
            logger.debug("Переменные окружения загружены")
            
            # Проверяем наличие необходимых переменных окружения
            if not os.getenv('OPENAI_API_KEY'):
                raise ValueError("Не найден OPENAI_API_KEY в переменных окружения")
            if not os.getenv('TELEGRAM_TOKEN'):
                raise ValueError("Не найден TELEGRAM_TOKEN в переменных окружения")
            
            # Инициализируем клиент OpenAI
            self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            logger.info("OpenAI клиент инициализирован")
            
            # Инициализируем клиент Telegram
            self.bot = telegram.Bot(token=os.getenv('TELEGRAM_TOKEN'))
            logger.info("Telegram бот инициализирован")
            
            # Инициализируем клиент Google Sheets
            self.sheets_api = GoogleSheetsAPI()
            logger.info("Google Sheets API клиент создан")
            
            # Аутентифицируемся в Google Sheets
            self.sheets_api.authenticate()
            logger.info("Успешная аутентификация в Google Sheets API")
            
            logger.info("CommandProcessor успешно инициализирован")
            
        except Exception as e:
            logger.error(f"Ошибка при инициализации CommandProcessor: {str(e)}")
            raise

    async def initialize(self) -> None:
        """Асинхронная инициализация и проверка подключений"""
        try:
            await self._check_telegram_connection()
        except Exception as e:
            logger.error(f"Ошибка при асинхронной инициализации: {str(e)}")
            raise

    async def _check_telegram_connection(self) -> None:
        """Проверяет подключение к Telegram API"""
        try:
            me = await self.bot.get_me()
            logger.info(f"Подключение к Telegram успешно. Имя бота: {me.first_name}")
        except Exception as e:
            logger.error(f"Ошибка подключения к Telegram: {str(e)}")
            raise

    def _extract_project_info(self, message: str) -> Tuple[Optional[str], Optional[List[str]]]:
        """
        Извлекает информацию о проекте из сообщения с помощью ChatGPT.
        
        Args:
            message: Текст сообщения от пользователя
            
        Returns:
            Tuple[Optional[str], Optional[List[str]]]: Кортеж (название проекта, список разделов)
        """
        try:
            logger.info(f"Начало извлечения информации из сообщения: {message}")
            
            # Формируем промпт для ChatGPT
            prompt = f"""
            Ты - помощник для извлечения информации о проекте из текста.
            
            Пользователь может использовать разные формулировки для создания проекта, например:
            - "Создай проект X с разделами A, B, C"
            - "Сделай таблицу X с разделами A и B"
            - "Нужна таблица для проекта X с разделами A, B"
            
            Тебе нужно извлечь:
            1. Название проекта
            2. Список разделов или категорий
            
            Если в тексте есть слова "с разделами", используй то что после них как разделы.
            Если разделы перечислены через "и" или запятую - раздели их.
            
            Верни ответ строго в формате JSON:
            {{
                "project_name": "название проекта",
                "sections": ["раздел1", "раздел2", ...]
            }}
            
            Примеры:
            
            Входное сообщение: 'Создай проект "Ремонт офиса" с разделами организация, материалы, работы'
            Ответ: {{"project_name": "Ремонт офиса", "sections": ["организация", "материалы", "работы"]}}
            
            Входное сообщение: 'Сделай таблицу Фестиваль красок с волонтерами и фотографами'
            Ответ: {{"project_name": "Фестиваль красок", "sections": ["волонтеры", "фотографы"]}}
            
            Если формат сообщения совсем не соответствует - верни null.
            
            Текст для обработки: {message}
            """
            
            logger.debug(f"Подготовлен промпт для ChatGPT: {prompt}")
            
            # Отправляем запрос в ChatGPT
            logger.info("Отправка запроса в ChatGPT API")
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты - помощник для извлечения структурированной информации из текста."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Парсим ответ
            result = json.loads(response.choices[0].message.content)
            logger.info(f"Получен и разобран ответ от ChatGPT: {json.dumps(result, ensure_ascii=False)}")
            
            # Проверяем корректность данных
            if not result or not result.get("project_name") or not result.get("sections"):
                logger.warning("ChatGPT вернул неполные данные или null")
                return None, None
            
            return result["project_name"], result["sections"]
            
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка при разборе JSON-ответа от ChatGPT: {str(e)}")
            return None, None
        except Exception as e:
            logger.error(f"Ошибка при извлечении информации из сообщения: {str(e)}")
            return None, None

    def process_command(self, message: str) -> str:
        """
        Обрабатывает команду пользователя.
        
        Args:
            message: Текст сообщения от пользователя
            
        Returns:
            str: Ответное сообщение для пользователя
        """
        try:
            logger.info(f"Начало обработки команды: {message}")
            
            # Извлекаем информацию о проекте
            logger.info("Извлечение информации о проекте из сообщения")
            project_name, sections = self._extract_project_info(message)
            
            if not project_name or not sections:
                error_msg = "Не удалось извлечь информацию о проекте из сообщения. Пожалуйста, сформулируйте иначе."
                logger.error(error_msg)
                return error_msg
            
            logger.info(f"Извлечена информация: project_name='{project_name}', sections={sections}")
            
            # Формируем данные проекта
            project_data = {
                "project_name": project_name,
                "sections": sections
            }
            
            logger.info(f"Создание листа проекта с данными: {json.dumps(project_data, ensure_ascii=False)}")
            
            try:
                # Создаем лист проекта
                sheet_id = self.sheets_api.create_project_sheet(project_data)
                logger.info(f"Лист проекта успешно создан с ID: {sheet_id}")
                
                success_message = f"""
                ✅ Лист проекта успешно создан!
                
                📋 Название проекта: {project_name}
                📑 Разделы: {', '.join(sections)}
                🔗 ID листа: {sheet_id}
                """
                
                logger.info("Команда успешно обработана")
                return success_message
            except Exception as sheet_error:
                error_msg = f"Ошибка при создании листа проекта: {str(sheet_error)}"
                logger.error(error_msg)
                return f"❌ {error_msg}"
            
        except Exception as e:
            error_msg = f"Ошибка при обработке команды: {str(e)}"
            logger.error(error_msg)
            return f"❌ {error_msg}"

    async def send_telegram_message(self, chat_id: int, text: str) -> None:
        """
        Отправляет сообщение пользователю в Telegram.
        
        Args:
            chat_id: ID чата
            text: Текст сообщения
        """
        try:
            await self.bot.send_message(chat_id=chat_id, text=text)
            logger.info(f"Сообщение успешно отправлено в чат {chat_id}")
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения в Telegram: {str(e)}")
            raise

    async def process_message(self, message: dict) -> None:
        """
        Обрабатывает сообщение от Telegram.
        
        Args:
            message: Словарь с данными сообщения от Telegram
        """
        try:
            logger.info("Начало обработки сообщения от Telegram")
            logger.debug(f"Получено сообщение: {message}")
            
            # Получаем текст сообщения и информацию о чате
            chat_id = message.chat["id"]
            text = message.text or ""
            
            if not chat_id or not text:
                logger.warning("Получено некорректное сообщение")
                return
                
            logger.info(f"Обработка сообщения от chat_id {chat_id}: {text}")
            
            # Если это команда /start
            if text == '/start':
                welcome_message = """
                👋 Привет! Я бот для создания проектных листов в Google Sheets.
                
                📝 Чтобы создать новый проект, напиши мне сообщение в формате:
                Создай проект "Название проекта" с разделами раздел1, раздел2, раздел3
                
                Например:
                Создай проект "Ремонт офиса" с разделами организация, материалы, работы
                """
                await self.send_telegram_message(chat_id, welcome_message)
                return
            
            # Обрабатываем команду создания проекта
            response = self.process_command(text)
            await self.send_telegram_message(chat_id, response)
            
            logger.info(f"Сообщение успешно обработано: {text}")
            
        except Exception as e:
            error_message = f"❌ Произошла ошибка при обработке команды: {str(e)}"
            logger.error(error_message)
            await self.send_telegram_message(chat_id, error_message)
