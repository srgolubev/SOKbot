from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os
import json
import datetime

# Определяем области доступа
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def test_sheets():
    try:
        # Загружаем токен
        token_path = os.path.join('credentials', 'token.json')
        with open(token_path, 'r') as token:
            creds_data = json.load(token)
            credentials = Credentials.from_authorized_user_info(creds_data, SCOPES)
        
        # Создаем сервис
        service = build('sheets', 'v4', credentials=credentials)
        
        # Создаем новую таблицу
        current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        spreadsheet_title = f"Тестовая таблица {current_time}"
        
        spreadsheet = {
            'properties': {
                'title': spreadsheet_title
            }
        }
        
        spreadsheet = service.spreadsheets().create(body=spreadsheet).execute()
        spreadsheet_id = spreadsheet.get('spreadsheetId')
        
        print(f"✅ Таблица успешно создана! ID: {spreadsheet_id}")
        print(f"🔗 Ссылка на таблицу: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
        
        # Добавляем тестовые данные
        values = [
            ["Имя", "Возраст", "Город"],
            ["Иван", "25", "Москва"],
            ["Мария", "30", "Санкт-Петербург"]
        ]
        
        range_name = "Лист1!A1:C3"
        body = {
            'values': values
        }
        
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()
        
        print("✅ Тестовые данные успешно добавлены")
        
    except Exception as e:
        print(f"❌ Произошла ошибка: {str(e)}")

if __name__ == "__main__":
    test_sheets()
