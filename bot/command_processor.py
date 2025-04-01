import os
import json
import logging
from typing import Dict, List, Tuple, Optional
from openai import OpenAI
from dotenv import load_dotenv
from .sheets_api import GoogleSheetsAPI

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
        
    async def initialize(self):
        """
        Асинхронная инициализация процессора команд.
        Этот метод вызывается при запуске приложения.
        """
        try:
            logger.info("Начало асинхронной инициализации CommandProcessor")
            
            # Загружаем переменные окружения
            load_dotenv()
            logger.debug("Переменные окружения загружены")
            
            # Проверяем наличие необходимых переменных окружения
            if not os.getenv('OPENAI_API_KEY'):
                raise ValueError("Не найден OPENAI_API_KEY в переменных окружения")
            
            if not os.getenv('TELEGRAM_BOT_TOKEN'):
                raise ValueError("Не найден TELEGRAM_BOT_TOKEN в переменных окружения")
            
            # Инициализируем клиент OpenAI, если он еще не инициализирован
            if not hasattr(self, 'openai_client') or self.openai_client is None:
                self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
                logger.info("OpenAI клиент инициализирован")
            
            # Инициализируем клиент Google Sheets, если он еще не инициализирован
            if not hasattr(self, 'sheets_api') or self.sheets_api is None:
                self.sheets_api = GoogleSheetsAPI()
                logger.info("Google Sheets API клиент создан")
                
                # Аутентифицируемся в Google Sheets
                self.sheets_api.authenticate()
                logger.info("Успешная аутентификация в Google Sheets API")
            
            # Инициализируем словарь для хранения истории сообщений, если он еще не инициализирован
            if not hasattr(self, 'chat_histories'):
                self.chat_histories = {}
                self.max_history_length = 5  # Уменьшено до 5 для оптимизации использования памяти
                logger.info("Инициализировано хранилище истории сообщений")
            
            logger.info("Асинхронная инициализация CommandProcessor успешно завершена")
            
        except Exception as e:
            logger.error(f"Ошибка при асинхронной инициализации CommandProcessor: {str(e)}")
            raise
        # Пустой конструктор, вся инициализация перенесена в метод initialize
        # Это позволяет использовать асинхронные операции при инициализации
        pass

    def _determine_intent(self, message: str) -> str:
        """
        Определяет тип запроса на основе ключевых слов
        
        Args:
            message: Текст сообщения от пользователя
            
        Returns:
            str: Тип запроса ("create_table", "help" или "chat")
        """
        logger.info(f"DEBUG: Определение типа запроса для сообщения: '{message}'")
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
        
        # Проверяем наличие ключевых слов
        for keyword in create_table_keywords:
            if keyword in message_lower:
                logger.info(f"DEBUG: Найдено ключевое слово для создания таблицы: '{keyword}'")
                return "create_table"
                
        for keyword in help_keywords:
            if keyword in message_lower:
                logger.info(f"DEBUG: Найдено ключевое слово для справки: '{keyword}'")
                return "help"
        
        logger.info("DEBUG: Ключевые слова не найдены, используем режим чата")
        return "chat"  # По умолчанию - режим чата
    
    def _chat_with_ai(self, message: str, chat_id: int) -> str:
        """
        Обрабатывает обычный запрос к AI через OpenAI API
        
        Args:
            message: Текст сообщения от пользователя
            chat_id: ID чата пользователя для хранения истории сообщений
            
        Returns:
            str: Ответ от AI
        """
        try:
            logger.info(f"DEBUG: Отправка запроса в OpenAI API для chat_id {chat_id}: '{message}'")
            
            # Системное сообщение для задания контекста
            system_message = {
                "role": "system", 
                "content": "Ты помощник в телеграм боте, который может отвечать на вопросы и помогать с различными задачами. Отвечай кратко и по существу."
            }
            
            # Инициализируем историю сообщений для нового пользователя
            if chat_id not in self.chat_histories:
                self.chat_histories[chat_id] = []
                logger.info(f"DEBUG: Создана новая история сообщений для chat_id {chat_id}")
            
            # Добавляем сообщение пользователя в историю
            self.chat_histories[chat_id].append({"role": "user", "content": message})
            
            # Ограничиваем размер истории, чтобы не превысить лимиты OpenAI
            if len(self.chat_histories[chat_id]) > self.max_history_length:
                # Удаляем самые старые сообщения, оставляя только последние max_history_length
                self.chat_histories[chat_id] = self.chat_histories[chat_id][-self.max_history_length:]
                logger.info(f"DEBUG: История сообщений для chat_id {chat_id} ограничена до {self.max_history_length} сообщений")
            
            # Формируем запрос к OpenAI API с историей сообщений
            messages = [system_message] + self.chat_histories[chat_id]
            logger.info(f"DEBUG: Отправка {len(messages)} сообщений в OpenAI API")
            
            # Логируем историю сообщений для отладки
            for i, msg in enumerate(self.chat_histories[chat_id]):
                logger.info(f"DEBUG: История [{i}] - {msg['role']}: {msg['content'][:30]}...")
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages
            )
            
            # Извлекаем текст ответа
            ai_response = response.choices[0].message.content
            logger.info(f"DEBUG: Получен ответ от OpenAI API: '{ai_response[:50]}...'")
            
            # Сохраняем ответ в истории
            self.chat_histories[chat_id].append({"role": "assistant", "content": ai_response})
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Ошибка при обращении к AI: {str(e)}")
            return "К сожалению, произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже."
    
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
            Извлеки из текста название проекта и список разделов.
            Верни ответ в формате JSON:
            {{
                "project_name": "название проекта",
                "sections": ["раздел1", "раздел2", ...]
            }}
            
            Текст: {message}
            """
            
            logger.debug(f"Подготовлен промпт для ChatGPT: {prompt}")
            
            # Отправляем запрос в ChatGPT
            logger.info("Отправка запроса в ChatGPT API")
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "Ты - помощник, который извлекает структурированную информацию из текста."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Добавляем логирование сырого ответа
            raw_content = response.choices[0].message.content
            logger.info(f"Сырой ответ от ChatGPT: {raw_content}")
            
            # Парсим ответ
            result = json.loads(raw_content)
            logger.info(f"Получен и разобран ответ от ChatGPT: {json.dumps(result, ensure_ascii=False)}")
            
            # Проверяем корректность данных
            if not result.get("project_name") or not result.get("sections"):
                raise ValueError("ChatGPT вернул неполные данные")
            
            return result["project_name"], result["sections"]
            
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка при разборе JSON-ответа от ChatGPT: {str(e)}")
            return None, None
        except Exception as e:
            logger.error(f"Ошибка при извлечении информации из сообщения: {str(e)}")
            return None, None

    def process_command(self, message: str, chat_id: int) -> str:
        """
        Обрабатывает команду пользователя.
        
        Args:
            message: Текст сообщения от пользователя
            chat_id: ID чата пользователя для хранения истории сообщений
            
        Returns:
            str: Ответное сообщение для пользователя
        """
        try:
            logger.info(f"DEBUG: Начало обработки команды: '{message}'")
            
            # Определяем тип запроса
            intent = self._determine_intent(message)
            logger.info(f"DEBUG: Определен тип запроса: {intent}")
            
            # Обрабатываем запрос в зависимости от его типа
            if intent == "create_table":
                logger.info("DEBUG: Обработка запроса на создание таблицы")
                # Извлекаем информацию о проекте
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
                
            elif intent == "help":
                logger.info("DEBUG: Обработка запроса на получение справки")
                # Отправляем справку
                help_text = """Я могу помочь вам с созданием таблиц Google Sheets для ваших проектов, а также отвечать на ваши вопросы.

Для создания таблицы просто напишите что-то вроде:
"Создай таблицу для проекта X с разделами A, B, C"

Для обычного общения просто задайте мне любой вопрос, и я постараюсь на него ответить.
"""
                return help_text
                
            else:  # intent == "chat"
                logger.info(f"DEBUG: Обработка запроса в режиме чата для chat_id {chat_id}")
                # Обрабатываем как обычный запрос к чат-боту
                ai_response = self._chat_with_ai(message, chat_id)
                return ai_response
            
        except Exception as e:
            error_msg = f"Ошибка при обработке команды: {str(e)}"
            logger.error(error_msg)
            return f"❌ {error_msg}"
    
    async def process_message(self, message) -> None:
        """
        Обрабатывает сообщение от Telegram.
        
        Args:
            message: Объект сообщения от Telegram
        """
        try:
            logger.info("Начало обработки сообщения от Telegram")
            
            # Логируем структуру объекта message для отладки
            logger.info(f"DEBUG: Структура объекта message: {dir(message)}")
            logger.info(f"DEBUG: Структура объекта message.chat: {message.chat}")
            
            # Получаем текст сообщения и информацию о чате
            chat_id = message.chat["id"]
            text = message.text or ""
            logger.info(f"DEBUG: Получен chat_id: {chat_id}, текст: '{text}'")
            
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
                
                Также ты можешь задать мне любой вопрос, и я постараюсь на него ответить!
                """
                await self.send_telegram_message(chat_id, welcome_message)
                return
            
            # Обрабатываем текст сообщения
            response = self.process_command(text, chat_id)
            
            # Отправляем ответ пользователю
            await self.send_telegram_message(chat_id, response)
            
            logger.info(f"Сообщение успешно обработано: {text}")
            
        except Exception as e:
            error_msg = f"Ошибка при обработке сообщения: {str(e)}"
            logger.error(error_msg)
            try:
                await self.send_telegram_message(message.chat["id"], f"❌ {error_msg}")
            except Exception as send_error:
                logger.error(f"Не удалось отправить сообщение об ошибке: {str(send_error)}")
    
    async def send_telegram_message(self, chat_id: int, text: str) -> None:
        """
        Отправляет сообщение в Telegram.
        
        Args:
            chat_id: ID чата
            text: Текст сообщения
        """
        try:
            import httpx
            from os import getenv
            
            bot_token = getenv('TELEGRAM_BOT_TOKEN')
            if not bot_token:
                raise ValueError("Не найден TELEGRAM_BOT_TOKEN в переменных окружения")
                
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data)
                response.raise_for_status()
                logger.info(f"HTTP Request: POST {url} \"{response.status_code} {response.reason_phrase}\"")
                
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения в Telegram: {str(e)}")
