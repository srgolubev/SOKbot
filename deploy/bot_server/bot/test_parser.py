from gpt_command_parser import GPTCommandParser
import json

def test_parser():
    parser = GPTCommandParser()
    
    # Тестовые команды
    test_commands = [
        "Создай проект Фестиваль ГТО с разделами аренда, судьи и звук",
        "Можешь сделать таблицу для проекта Марафон? Нужны такие разделы: регистрация участников, медицинский контроль, награждение",
        "Помоги организовать конференцию IT Future, разделы: регистрация, кейтеринг, техническое оснащение, спикеры",
        "Привет, как дела?",  # Не команда создания таблицы
        "Сделай пожалуйста таблицу, название Детский праздник, а разделы будут: аниматоры, декор, фотограф, торт"
    ]
    
    print("Тестирование парсера команд:")
    for cmd in test_commands:
        print(f"\nКоманда: {cmd}")
        result = parser.parse_command(cmd)
        print(f"Результат: {json.dumps(result, ensure_ascii=False, indent=2)}")

if __name__ == "__main__":
    test_parser()
