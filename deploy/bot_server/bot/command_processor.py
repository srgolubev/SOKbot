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
        try:
            logger.info("Начало инициализации CommandProcessor")
            
            # Загружаем переменные окружения
            load_dotenv()
            logger.debug("Переменные окружения загружены")
            
            # Проверяем наличие необходимых переменных окружения
            if not os.getenv('OPENAI_API_KEY'):
                raise ValueError("Не найден OPENAI_API_KEY в переменных окружения")
            
            # Инициализируем клиент OpenAI
            self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            logger.info("OpenAI клиент инициализирован")
            
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
    
    def _chat_with_ai(self, message: str) -> str:
        """
        Обрабатывает обычный запрос к AI через OpenAI API
        
        Args:
            message: Текст сообщения от пользователя
            
        Returns:
            str: Ответ от AI
        """
        try:
            logger.info(f"DEBUG: Отправка запроса в OpenAI API: '{message}'")
            
            # Формируем запрос к OpenAI API
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты помощник в телеграм боте, который может отвечать на вопросы и помогать с различными задачами. Отвечай кратко и по существу."},
                    {"role": "user", "content": message}
                ]
            )
            
            # Извлекаем текст ответа
            ai_response = response.choices[0].message.content
            logger.info(f"DEBUG: Получен ответ от OpenAI API: '{ai_response[:50]}...'")
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
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты - помощник, который извлекает структурированную информацию из текста."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Парсим ответ
            result = json.loads(response.choices[0].message.content)
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

    def process_command(self, message: str) -> str:
        """
        Обрабатывает команду пользователя.
        
        Args:
            message: Текст сообщения от пользователя
            
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
                logger.info("DEBUG: Обработка запроса в режиме чата")
                # Обрабатываем как обычный запрос к чат-боту
                ai_response = self._chat_with_ai(message)
                return ai_response
            
        except Exception as e:
            error_msg = f"Ошибка при обработке команды: {str(e)}"
            logger.error(error_msg)
            return f"❌ {error_msg}"
