import sys
import os

# Добавляем путь к корневой директории проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.sheets_api import GoogleSheetsAPI
import datetime

def test_sheets_api():
    # Создаем экземпляр API
    api = GoogleSheetsAPI()
    
    # Аутентифицируемся
    api.authenticate()
    
    # Создаем новую таблицу с текущей датой в названии
    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    spreadsheet_title = f"Тестовая таблица {current_time}"
    
    try:
        # Создаем таблицу
        spreadsheet_id = api.create_spreadsheet(spreadsheet_title)
        print(f"✅ Таблица успешно создана! ID: {spreadsheet_id}")
        print(f"🔗 Ссылка на таблицу: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
        
        # Добавляем тестовые данные
        values = [
            ["Имя", "Возраст", "Город"],
            ["Иван", "25", "Москва"],
            ["Мария", "30", "Санкт-Петербург"]
        ]
        
        range_name = "Лист1!A1:C3"
        api.update_values(spreadsheet_id, range_name, values)
        print("✅ Тестовые данные успешно добавлены")
        
    except Exception as e:
        print(f"❌ Произошла ошибка: {str(e)}")

if __name__ == "__main__":
    test_sheets_api()
