import re
import json
from typing import Dict, List, Optional

class CommandParser:
    """
    Класс для парсинга команд пользователя с использованием регулярных выражений
    и базовых техник обработки естественного языка
    """
    
    def __init__(self):
        # Шаблон для извлечения названия проекта
        # Ищет текст между "таблицу" и "добавь разделы" или "," или конец строки
        self.project_pattern = r'(?:таблицу\s+)([^,]+?)(?:\s*,\s*добавь\s+разделы|\s*$)'
        
        # Шаблон для извлечения разделов
        # Ищет текст после "разделы" до конца строки и разбивает по запятой
        self.sections_pattern = r'(?:разделы\s+)(.+)$'

    def clean_text(self, text: str) -> str:
        """
        Очищает текст от лишних пробелов и приводит к нижнему регистру
        
        Args:
            text (str): Исходный текст
            
        Returns:
            str: Очищенный текст
        """
        # Удаляем множественные пробелы и переносы строк
        text = re.sub(r'\s+', ' ', text)
        # Приводим к нижнему регистру
        text = text.lower().strip()
        return text

    def extract_project_name(self, text: str) -> Optional[str]:
        """
        Извлекает название проекта из команды
        
        Args:
            text (str): Текст команды
            
        Returns:
            Optional[str]: Название проекта или None, если не найдено
        """
        match = re.search(self.project_pattern, text)
        if match:
            # Очищаем название проекта от лишних пробелов
            return match.group(1).strip()
        return None

    def extract_sections(self, text: str) -> List[str]:
        """
        Извлекает список разделов из команды
        
        Args:
            text (str): Текст команды
            
        Returns:
            List[str]: Список разделов
        """
        match = re.search(self.sections_pattern, text)
        if match:
            # Разбиваем по запятой и очищаем каждый раздел
            sections = [
                section.strip()
                for section in match.group(1).split(',')
                if section.strip()
            ]
            return sections
        return []

    def parse_command(self, command: str) -> Dict[str, any]:
        """
        Парсит команду и возвращает структурированный результат
        
        Args:
            command (str): Текст команды
            
        Returns:
            Dict[str, any]: Словарь с названием проекта и списком разделов
        """
        # Очищаем текст команды
        cleaned_command = self.clean_text(command)
        
        # Извлекаем название проекта и разделы
        project_name = self.extract_project_name(cleaned_command)
        sections = self.extract_sections(cleaned_command)
        
        # Формируем результат
        result = {
            "project_name": project_name,
            "sections": sections
        }
        
        return result

def test_parser():
    """
    Тестирование парсера на примере команды
    """
    # Создаем экземпляр парсера
    parser = CommandParser()
    
    # Тестовая команда
    test_command = '@бот, создай таблицу Фестиваль гто, добавь разделы аренда, судьи, звук, свет, сцена, сувенирка, наградная'
    
    # Парсим команду
    result = parser.parse_command(test_command)
    
    # Выводим результат
    print("Тест парсера команд:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # Проверяем корректность
    assert result["project_name"] == "фестиваль гто"
    assert len(result["sections"]) == 7
    assert "аренда" in result["sections"]
    print("Все тесты пройдены успешно!")

if __name__ == "__main__":
    test_parser()
