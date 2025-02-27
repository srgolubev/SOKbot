from google_auth_oauthlib.flow import InstalledAppFlow
import os

# Определяем области доступа
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def generate_token():
    """Генерирует токен для Google Sheets API"""
    client_secrets_file = os.path.join('credentials', 'client_secrets.json')
    
    # Запускаем процесс OAuth 2.0
    flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
    credentials = flow.run_local_server(port=0)
    
    # Сохраняем токен
    token_path = os.path.join('credentials', 'token.json')
    with open(token_path, 'w') as token:
        token.write(credentials.to_json())
    print(f"Токен успешно сохранен в {token_path}")

if __name__ == "__main__":
    generate_token()
