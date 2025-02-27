import unittest
import os
import json
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bot.gpt_command_parser import GPTCommandParser, ParsingError

class TestGPTCommandParser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Инициализация парсера перед всеми тестами"""
        load_dotenv()
        cls.parser = GPTCommandParser()

    def test_valid_create_project_commands(self):
        """Тест корректных команд создания проекта"""
        test_cases = [
            {
                "input": "Создай проект Фестиваль ГТО с разделами аренда, судьи и звук",
                "expected": {
                    "project_name": "Фестиваль ГТО",
                    "sections": ["аренда", "судьи", "звук"],
                    "is_create_table_command": True
                }
            },
            {
                "input": "Нужна таблица для проекта День города, разделы: сцена, свет, звук",
                "expected": {
                    "project_name": "День города",
                    "sections": ["сцена", "свет", "звук"],
                    "is_create_table_command": True
                }
            },
            {
                "input": "Создай таблицу для проекта Марафон 2025 с разделами регистрация и награждение",
                "expected": {
                    "project_name": "Марафон 2025",
                    "sections": ["регистрация", "награждение"],
                    "is_create_table_command": True
                }
            }
        ]

        for case in test_cases:
            with self.subTest(input=case["input"]):
                result = self.parser.parse_command(case["input"])
                self.assertEqual(result["project_name"], case["expected"]["project_name"])
                self.assertEqual(set(result["sections"]), set(case["expected"]["sections"]))
                self.assertTrue(result["is_create_table_command"])

    def test_invalid_commands(self):
        """Тест некорректных команд"""
        test_cases = [
            "Привет, как дела?",
            "Что ты умеешь?",
            "Покажи список проектов"
        ]

        for command in test_cases:
            with self.subTest(command=command):
                result = self.parser.parse_command(command)
                self.assertFalse(result["is_create_table_command"])
                self.assertEqual(result["project_name"], "")
                self.assertEqual(result["sections"], [])

    def test_partial_commands(self):
        """Тест частичных команд (с отсутствующими данными)"""
        test_cases = [
            {
                "input": "Создай проект Фестиваль",
                "expected": {
                    "project_name": "Фестиваль",
                    "sections": [],
                    "is_create_table_command": True
                }
            },
            {
                "input": "Нужны разделы: музыка, свет",
                "expected": {
                    "project_name": "",
                    "sections": ["музыка", "свет"],
                    "is_create_table_command": False
                }
            }
        ]

        for case in test_cases:
            with self.subTest(input=case["input"]):
                result = self.parser.parse_command(case["input"])
                self.assertEqual(result["project_name"], case["expected"]["project_name"])
                self.assertEqual(set(result["sections"]), set(case["expected"]["sections"]))
                self.assertEqual(result["is_create_table_command"], case["expected"]["is_create_table_command"])

    def test_edge_cases(self):
        """Тест граничных случаев"""
        test_cases = [
            {"input": "", "should_raise": True},
            {"input": None, "should_raise": True},
            {"input": "   ", "should_raise": True},
            {
                "input": "Создай проект с очень-очень-очень-очень-очень длинным названием и большим количеством разделов: раздел1, раздел2, раздел3, раздел4, раздел5, раздел6, раздел7, раздел8, раздел9, раздел10",
                "should_raise": False
            }
        ]

        for case in test_cases:
            with self.subTest(input=case["input"]):
                if case["should_raise"]:
                    with self.assertRaises(ParsingError):
                        self.parser.parse_command(case["input"])
                else:
                    try:
                        result = self.parser.parse_command(case["input"])
                        self.assertIsInstance(result, dict)
                        self.assertIn("project_name", result)
                        self.assertIn("sections", result)
                        self.assertIn("is_create_table_command", result)
                    except Exception as e:
                        self.fail(f"Неожиданная ошибка: {str(e)}")

    def test_response_validation(self):
        """Тест валидации ответа"""
        invalid_responses = [
            {},  # Пустой словарь
            {"project_name": "Test"},  # Отсутствуют обязательные поля
            {"project_name": "Test", "sections": "not a list", "is_create_table_command": True},  # Неверный тип данных
            {"project_name": 123, "sections": [], "is_create_table_command": True},  # Неверный тип данных
            {"project_name": "Test", "sections": [], "is_create_table_command": "true"}  # Неверный тип данных
        ]

        for response in invalid_responses:
            with self.subTest(response=response):
                with self.assertRaises(ParsingError):
                    self.parser.validate_response(response)

if __name__ == '__main__':
    unittest.main()
