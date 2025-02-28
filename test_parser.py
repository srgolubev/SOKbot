import asyncio
from bot.gpt_command_parser import GPTCommandParser

async def main():
    parser = GPTCommandParser()
    
    test_commands = [
        "Создай проект Фестиваль ГТО с разделами аренда, судьи и звук",
        "У нас новый проект Кожаный мяч 2027. Нужны будут флаги, сувенирка, шатры",
        "Начинаем проект Марафон 2024, потребуются: регистрация, питание, медики",
        "Нужна таблица для проекта День города: сцена, свет, звук",
        "Создай проект Городской праздник"
    ]
    
    for command in test_commands:
        print(f"\nТестируем команду: {command}")
        try:
            result = await parser.parse_command(command)
            print(f"Результат:")
            print(f"  Название проекта: {result['project_name']}")
            print(f"  Разделы: {', '.join(result['sections'])}")
            print(f"  Создать таблицу: {result['is_create_table_command']}")
        except Exception as e:
            print(f"Ошибка: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
