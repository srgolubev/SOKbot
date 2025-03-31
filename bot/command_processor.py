import os
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
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
    def _determine_intent(self, message: str) -> str:
        """
        Определяет тип запроса на основе ключевых слов
        
        Args:
            message: Текст сообщения от пользователя
            
        Returns:
            str: Тип запроса ("create_table", "help" или "chat")
        """
        message_lower = message.lower()
        
        # Ключевые слова для создания таблицы
        create_table_keywords = [
            "создай таблицу", "сделай таблицу", "новая таблица", 
            "создать таблицу", "сделать таблицу", "создай лист", "сделай лист"
        ]
        
        # Ключевые слова для запроса помощи
        help_keywords = [
            "помощь", "справка", "как использовать", "что ты умеешь", 
            "как работает", "команды", "инструкция"
        ]
        
        if any(keyword in message_lower for keyword in create_table_keywords):
            return "create_table"
        elif any(keyword in message_lower for keyword in help_keywords):
            return "help"
        else:
            return "chat"  # По умолчанию - режим чата
    
    def _extract_project_info(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Извлекает информацию о проекте из сообщения пользователя используя GPT
        
        Args:
            message: Текст сообщения от пользователя
            
        Returns:
            Optional[Dict[str, Any]]: Словарь с информацией о проекте или None в случае ошибки
        """
        try:
            prompt = f"""
            Извлеки из текста название проекта и список разделов для создания таблицы.
            Разделы должны быть релевантны контексту проекта.
            
            Текст: {message}
            
            Ответь строго в формате JSON:
            {{
                "project_name": "Название проекта",
                "sections": ["Раздел 1", "Раздел 2", ...]
            }}
            """
            
            # Синхронный вызов OpenAI API (без await)
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo-1106",
                response_format={ "type": "json_object" },
                messages=[
                    {"role": "system", "content": "Ты помощник для извлечения информации о проекте из текста"},
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Извлекаем JSON из ответа
            result = json.loads(response.choices[0].message.content)
            
            # Проверяем обязательные поля
            if not result.get('project_name') or not result.get('sections'):
                logger.error("GPT вернул неполный ответ")
                return None
                
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении информации из сообщения: {str(e)}")
            return None
            
    def _chat_with_ai(self, message: str) -> str:
        """
        Обрабатывает обычный запрос к AI через OpenAI API
        
        Args:
            message: Текст сообщения от пользователя
            
        Returns:
            str: Ответ от AI
        """
        try:
            # Синхронный вызов OpenAI API
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты помощник в телеграм боте, который может отвечать на вопросы и помогать с различными задачами. Отвечай кратко и по существу."},
                    {"role": "user", "content": message}
                ]
            )
            
            # Извлекаем текст ответа
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Ошибка при обращении к AI: {str(e)}")
            return "К сожалению, произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже."

    # async def _extract_project_info(self, message: str) -> Optional[Dict[str, Any]]:
    #     """
    #     Извлекает информацию о проекте из сообщения пользователя используя GPT
        
    #     Args:
    #         message: Текст сообщения от пользователя
            
    #     Returns:
    #         Optional[Dict[str, Any]]: Словарь с информацией о проекте или None в случае ошибки
    #     """
    #     try:
    #         prompt = f"""
    #         Извлеки из текста название проекта и список разделов для создания таблицы.
    #         Разделы должны быть релевантны контексту проекта.
            
    #         Текст: {message}
            
    #         Ответь строго в формате JSON:
    #         {{
    #             "project_name": "Название проекта",
    #             "sections": ["Раздел 1", "Раздел 2", ...]
    #         }}
    #         """
            
    #         response = await self.openai_client.chat.completions.create(
    #             model="gpt-3.5-turbo-1106",
    #             response_format={ "type": "json_object" },
    #             messages=[
    #                 {"role": "system", "content": "Ты помощник для извлечения информации о проекте из текста"},
    #                 {"role": "user", "content": prompt}
    #             ]
    #         )
            
    #         # Извлекаем JSON из ответа
    #         result = json.loads(response.choices[0].message.content)
            
    #         # Проверяем обязательные поля
    #         if not result.get('project_name') or not result.get('sections'):
    #             logger.error("GPT вернул неполный ответ")
    #             return None
                
    #         return result
            
    #     except Exception as e:
    #         logger.error(f"Ошибка при извлечении информации из сообщения: {str(e)}")
    #         return None

    async def process_command(self, chat_id: int, command: str) -> None:
        """
        Обрабатывает команду от пользователя
        
        Args:
            chat_id: ID чата
            command: Текст команды
        """
        try:
            # Определяем тип запроса
            intent = self._determine_intent(command)
            logger.info(f"Определен тип запроса: {intent}")
            
            if intent == "create_table":
                # Извлекаем информацию о проекте из команды
                project_info = self._extract_project_info(command)
                if not project_info:
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text="Не удалось извлечь информацию о проекте из команды. Пожалуйста, попробуйте переформулировать."
                    )
                    return

                project_name = project_info['project_name']
                sections = project_info['sections']

                # Создаем лист проекта
                sheet_url = self.sheets_api.create_project_sheet_with_retry(project_name, sections)
                if sheet_url:
                    # Получаем фактическое имя листа из URL
                    sheet_name = sheet_url.split('=')[-1]  # Получаем gid
                    sheet_info = self.sheets_api.get_sheet_info(sheet_name)
                    actual_name = sheet_info['title'] if sheet_info else project_name
                    
                    message = f"Создан новый лист проекта"
                    if actual_name != project_name:
                        message += f" (имя изменено на '{actual_name}', так как '{project_name}' уже существует)"
                    message += f".\
Ссылка: {sheet_url}"
                    
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=message
                    )
                else:
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=f"Не удалось создать лист проекта. Пожалуйста, попробуйте позже."
                    )
            
            elif intent == "help":
                # Отправляем справку
                help_text = """Я могу помочь вам с созданием таблиц Google Sheets для ваших проектов, а также отвечать на ваши вопросы.

Для создания таблицы просто напишите что-то вроде:
"Создай таблицу для проекта X с разделами A, B, C"

Для обычного общения просто задайте мне любой вопрос, и я постараюсь на него ответить.
"""
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=help_text
                )
            
            else:  # intent == "chat"
                # Обрабатываем как обычный запрос к чат-боту
                ai_response = self._chat_with_ai(command)
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=ai_response
                )

        except Exception as e:
            logger.error(f"Ошибка при обработке команды: {str(e)}")
            await self.bot.send_message(
                chat_id=chat_id,
                text="Произошла ошибка при обработке команды. Пожалуйста, попробуйте позже."
            )

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
            await self.process_command(chat_id, text)
            
            logger.info(f"Сообщение успешно обработано: {text}")
            
        except Exception as e:
            error_message = f"❌ Произошла ошибка при обработке команды: {str(e)}"
            logger.error(error_message)
            await self.send_telegram_message(chat_id, error_message)
