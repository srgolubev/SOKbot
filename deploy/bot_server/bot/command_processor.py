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
            # Прямые команды на создание
            "создай таблицу", "сделай таблицу", "новая таблица", 
            "создать таблицу", "сделать таблицу", "создай лист", "сделай лист",
            # Дополнительные варианты
            "подготовь таблицу", "подготовить таблицу", "сформируй таблицу",
            "организуй таблицу", "составь таблицу", "составить таблицу",
            # Варианты с проектом
            "таблицу к проекту", "таблицу для проекта", "проект с разделами",
            # Дополнительные команды
            "добавь таблицу", "добавить таблицу"
        ]
        
        # Ключевые слова для запроса помощи
        help_keywords = [
            "помощь", "справка", "как использовать", "что ты умеешь", 
            "как работает", "команды", "инструкция"
        ]
        
        # Проверяем наличие ключевых слов для создания таблицы
        for keyword in create_table_keywords:
            if keyword in message_lower:
                logger.info(f"DEBUG: Найдено ключевое слово для создания таблицы: '{keyword}'")
                return "create_table"
        
        # Дополнительная проверка на наличие слова "таблица" и упоминания разделов
        if "таблиц" in message_lower and ("раздел" in message_lower or "секци" in message_lower):
            logger.info(f"DEBUG: Обнаружено упоминание таблицы и разделов")
            return "create_table"
        
        # Дополнительная проверка на наличие слова "проект" и упоминания разделов
        if "проект" in message_lower and ("раздел" in message_lower or "секци" in message_lower):
            logger.info(f"DEBUG: Обнаружено упоминание проекта и разделов")
            return "create_table"
        
        # Проверка на опечатки в слове "проект" с разделами
        if ("прект" in message_lower or "праект" in message_lower) and "раздел" in message_lower:
            logger.info(f"DEBUG: Обнаружена опечатка в слове 'проект' с упоминанием разделов")
            return "create_table"
        
        # Исключаем вопросы о проектах и таблицах
        question_markers = ["что такое", "что ты знаешь", "расскажи о", "что значит"]
        for marker in question_markers:
            if marker in message_lower and ("проект" in message_lower or "таблиц" in message_lower):
                logger.info(f"DEBUG: Обнаружен вопрос о проекте или таблице, используем режим чата")
                return "chat"
                
        # Проверяем наличие ключевых слов для справки
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
    
    def _extract_project_info(self, message: str) -> Dict[str, any]:
        """
        Извлекает информацию о проекте из сообщения с помощью ChatGPT.
        
        Args:
            message: Текст сообщения от пользователя
            
        Returns:
            Dict[str, any]: Словарь с информацией о проекте или пустой словарь в случае ошибки
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
            
            # Отправляем запрос в ChatGPT с обработкой ошибок
            try:
                logger.info("Отправка запроса в ChatGPT API")
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": "Ты - помощник, который извлекает структурированную информацию из текста."},
                        {"role": "user", "content": prompt}
                    ],
                    timeout=30  # Добавляем таймаут для запроса
                )
            except Exception as e:
                logger.error(f"Ошибка при запросе к ChatGPT API: {str(e)}")
                return {}
            
            # Проверяем ответ на наличие данных
            if not response or not response.choices or not response.choices[0].message:
                logger.error("ChatGPT вернул пустой ответ")
                return {}
            
            # Добавляем логирование сырого ответа
            raw_content = response.choices[0].message.content
            logger.info(f"Сырой ответ от ChatGPT: {raw_content}")
            
            # Парсим ответ с обработкой ошибок
            try:
                result = json.loads(raw_content)
                logger.info(f"Получен и разобран ответ от ChatGPT: {json.dumps(result, ensure_ascii=False)}")
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка при разборе JSON-ответа от ChatGPT: {str(e)}")
                return {}
            
            # Проверяем корректность данных
            if not isinstance(result, dict):
                logger.error(f"ChatGPT вернул некорректный формат данных: {type(result)}")
                return {}
            
            if not result.get("project_name") or not result.get("sections"):
                logger.error(f"ChatGPT вернул неполные данные: {result}")
                return {}
                
            if not isinstance(result.get("sections"), list):
                logger.error(f"ChatGPT вернул некорректный формат для разделов: {result.get('sections')}")
                return {}
            
            # Все проверки пройдены, возвращаем результат
            logger.info(f"Извлечена информация: project_name='{result['project_name']}', sections={result['sections']}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении информации из сообщения: {str(e)}")
            return {}

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
                project_data = self._extract_project_info(message)
                
                if not project_data or not project_data.get("project_name") or not project_data.get("sections"):
                    error_msg = "Не удалось извлечь информацию о проекте из сообщения. Пожалуйста, сформулируйте иначе."
                    logger.error(error_msg)
                    return error_msg
                
                logger.info(f"Создание листа проекта с данными: {json.dumps(project_data, ensure_ascii=False)}")
                
                # Отправляем сообщение о начале создания таблицы
                processing_message = f"""
                🔄 Начинаю создание таблицы...
                
                📋 Название проекта: {project_data['project_name']}
                📑 Разделы: {', '.join(project_data['sections'])}
                
                Это может занять некоторое время. Я сообщу, когда таблица будет готова.
                """
                
                # Импортируем asyncio до его использования
                import asyncio
                
                # Отправляем сообщение о начале создания немедленно
                asyncio.create_task(self.send_telegram_message(chat_id, processing_message))
                
                # Запускаем асинхронную задачу создания таблицы
                asyncio.create_task(self._create_table_async(chat_id, project_data))
                
                # Возвращаем пустое сообщение, т.к. мы уже отправили уведомление
                return ""
                
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
    
    async def _create_table_async(self, chat_id: int, project_data: dict) -> None:
        """
        Асинхронно создает таблицу и отправляет уведомление пользователю.
        
        Args:
            chat_id: ID чата пользователя
            project_data: Данные проекта для создания таблицы
        """
        try:
            logger.info(f"Начало асинхронного создания таблицы: {json.dumps(project_data, ensure_ascii=False)}")
            
            # Создаем лист проекта
            sheet_url = self.sheets_api.create_project_sheet_with_retry(project_data['project_name'], project_data['sections'])
            
            if sheet_url:
                logger.info(f"Таблица успешно создана: {sheet_url}")
                
                success_message = f"""
                ✅ Таблица успешно создана!
                
                📋 Название проекта: {project_data['project_name']}
                📑 Разделы: {', '.join(project_data['sections'])}
                🔗 Ссылка: {sheet_url}
                """
                
                await self.send_telegram_message(chat_id, success_message)
            else:
                logger.error("Не удалось создать таблицу")
                await self.send_telegram_message(chat_id, "❌ Не удалось создать таблицу. Пожалуйста, попробуйте позже.")
        except Exception as e:
            logger.error(f"Ошибка при асинхронном создании таблицы: {str(e)}")
            await self.send_telegram_message(chat_id, f"❌ Произошла ошибка при создании таблицы: {str(e)[:100]}... Пожалуйста, попробуйте позже.")
    
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
