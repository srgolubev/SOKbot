import json
import os
import logging
from typing import Dict, Any
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv

# Настройка логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Создаем обработчик для записи в файл
file_handler = logging.FileHandler('bot_parser.log', encoding='utf-8')
file_handler.setLevel(logging.INFO)

# Создаем форматтер
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Добавляем обработчик к логгеру
logger.addHandler(file_handler)

class ParsingError(Exception):
    """Исключение для ошибок парсинга команд"""
    pass

class GPTCommandParser:
    def __init__(self):
        try:
            load_dotenv()
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY не найден в переменных окружения")
            self.client = AsyncOpenAI(api_key=api_key)
            logger.info("GPT парсер успешно инициализирован")
        except Exception as e:
            logger.error(f"Ошибка при инициализации GPT парсера: {str(e)}")
            raise

        self.system_prompt = """
        Ты - помощник для анализа команд пользователя в Telegram боте.
        Твоя задача - извлекать из сообщений пользователя информацию о проектах и их разделах.
        
        Пользователь может писать команды в свободной форме, например:
        - "Создай проект Фестиваль ГТО с разделами аренда, судьи и звук"
        - "Нужна таблица для проекта День города, разделы: сцена, свет, звук"
        - "У нас новый проект Кожаный мяч 2027. Нужны будут флаги, сувенирка, шатры"
        - "Начинаем проект Марафон 2024, потребуются: регистрация, питание, медики"
        
        Правила обработки команд:
        1. ВСЕГДА устанавливай is_create_table_command в true, если:
           - В сообщении есть фразы "новый проект", "создай проект", "нужна таблица", "начинаем проект"
           - ИЛИ упоминается название проекта с последующим списком разделов/нужных вещей
           - ИЛИ просто упоминается название проекта (считаем, что пользователь хочет создать таблицу)
        2. Название проекта - это основное существительное с возможными определениями и годом
        3. Разделы - это всё, что идёт после фраз "нужны", "нужно", "потребуются", "с разделами", "разделы" или после двоеточия
        4. Если проект не найден - верни пустую строку в project_name
        5. Если разделы не найдены - верни пустой список в sections
        6. Даже если команда неполная (например, есть только название проекта без разделов), всё равно обрабатывай её
        
        ВСЕГДА возвращай JSON строго в таком формате:
        {
            "project_name": "название проекта",
            "sections": ["раздел1", "раздел2", ...],
            "is_create_table_command": true/false
        }
        """

    def validate_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Проверяет и нормализует ответ от GPT
        
        Args:
            response: Ответ от GPT в формате словаря
            
        Returns:
            Dict[str, Any]: Проверенный и нормализованный ответ
            
        Raises:
            ParsingError: Если ответ не соответствует ожидаемому формату
        """
        required_fields = {
            "project_name": str,
            "sections": list,
            "is_create_table_command": bool
        }
        
        # Проверяем наличие всех необходимых полей
        for field, field_type in required_fields.items():
            if field not in response:
                raise ParsingError(f"В ответе отсутствует поле {field}")
            if not isinstance(response[field], field_type):
                raise ParsingError(f"Поле {field} имеет неверный тип")
                
        # Проверяем, что все элементы в sections являются строками
        if response["sections"] and not all(isinstance(s, str) for s in response["sections"]):
            raise ParsingError("Все элементы в sections должны быть строками")
            
        return response

    async def parse_command(self, message: str) -> Dict[str, Any]:
        """
        Анализирует команду пользователя с помощью ChatGPT
        
        Args:
            message (str): Сообщение от пользователя
            
        Returns:
            Dict[str, Any]: Результат анализа в формате JSON
            
        Raises:
            ParsingError: При ошибках парсинга или некорректном ответе от API
        """
        try:
            logger.info(f"Начало парсинга команды: {message}")
            
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": message}
                ]
            )
            
            # Получаем ответ от GPT
            try:
                result = json.loads(response.choices[0].message.content)
                logger.info(f"Получен ответ от GPT: {result}")
            except json.JSONDecodeError as e:
                raise ParsingError(f"Ошибка при разборе JSON ответа: {str(e)}")
            
            # Проверяем и нормализуем ответ
            validated_result = self.validate_response(result)
            logger.info(f"Команда успешно разобрана: {validated_result}")
            
            return validated_result
            
        except Exception as e:
            error_msg = f"Неожиданная ошибка при обработке команды: {str(e)}"
            logger.error(error_msg)
            raise ParsingError(error_msg)

# Пример использования
if __name__ == "__main__":
    try:
        parser = GPTCommandParser()
        
        # Тестовые команды
        test_commands = [
            "Создай проект Фестиваль ГТО с разделами аренда, судьи и звук",
            "У нас новый проект Кожаный мяч 2027. Нужны будут флаги, сувенирка, шатры",
            "Как дела?",  # Не команда создания таблицы
        ]
        
        print("Тестирование парсера команд:")
        for cmd in test_commands:
            try:
                print(f"\nКоманда: {cmd}")
                result = parser.parse_command(cmd)
                print(f"Результат: {json.dumps(result, ensure_ascii=False, indent=2)}")
            except ParsingError as e:
                print(f"Ошибка при обработке команды: {str(e)}")
                
    except Exception as e:
        print(f"Критическая ошибка: {str(e)}")
        logger.critical(f"Критическая ошибка при тестировании: {str(e)}")
