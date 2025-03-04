import os
import json
import logging
import time
from typing import Optional, List
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Настройка логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Создаем обработчик для записи в файл
file_handler = logging.FileHandler('sheets_api.log', encoding='utf-8')
file_handler.setLevel(logging.INFO)

# Создаем форматтер
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Добавляем обработчик к логгеру
logger.addHandler(file_handler)

# Определяем области доступа
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',  # Полный доступ к таблицам
]

class GoogleSheetsAPI:
    def __init__(self):
        """Инициализация класса для работы с Google Sheets API"""
        self.credentials = None
        self.service = None
        self.spreadsheet_id = None
        
        # Путь к файлу с учетными данными сервисного аккаунта
        self.credentials_file = os.path.join('credentials', 'credentials.json')
        if not os.path.exists(self.credentials_file):
            raise FileNotFoundError(f"Файл {self.credentials_file} не найден")

    def authenticate(self) -> None:
        """
        Выполняет аутентификацию с Google Sheets API через сервисный аккаунт
        """
        try:
            logger.info("Начало аутентификации через сервисный аккаунт")
            
            # Загружаем учетные данные сервисного аккаунта
            from google.oauth2.service_account import Credentials
            self.credentials = Credentials.from_service_account_file(
                self.credentials_file,
                scopes=SCOPES
            )
            logger.info("Учетные данные сервисного аккаунта успешно загружены")
            
            # Создаем сервисный объект
            self.service = build('sheets', 'v4', credentials=self.credentials)
            logger.info("Сервисный объект успешно создан")
            
        except Exception as e:
            logger.error(f"Ошибка при аутентификации: {str(e)}")
            raise

    def get_service(self):
        """
        Возвращает сервисный объект для работы с Google Sheets API
        
        Returns:
            Resource: Сервисный объект Google Sheets API
            
        Raises:
            Exception: Если сервисный объект не был создан
        """
        if not self.service:
            raise Exception("Сервисный объект не создан. Сначала выполните authenticate()")
        return self.service

    def create_spreadsheet(self, title: str) -> str:
        """
        Создает новую таблицу Google Sheets
        
        Args:
            title: Название таблицы
            
        Returns:
            str: ID созданной таблицы
        """
        try:
            spreadsheet = {
                'properties': {
                    'title': title
                }
            }
            spreadsheet = self.service.spreadsheets().create(body=spreadsheet).execute()
            spreadsheet_id = spreadsheet.get('spreadsheetId')
            logger.info(f"Создана новая таблица с ID: {spreadsheet_id}")
            return spreadsheet_id
            
        except Exception as e:
            logger.error(f"Ошибка при создании таблицы: {str(e)}")
            raise

    def write_values(self, spreadsheet_id: str, range_name: str, values: list) -> None:
        """
        Записывает значения в указанный диапазон таблицы
        
        Args:
            spreadsheet_id: ID таблицы
            range_name: Диапазон для записи (например, 'Sheet1!A1:B2')
            values: Список списков с данными для записи
        """
        try:
            body = {
                'values': values
            }
            self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            logger.info(f"Данные успешно записаны в диапазон {range_name}")
            
        except Exception as e:
            logger.error(f"Ошибка при записи данных: {str(e)}")
            raise

    def read_values(self, spreadsheet_id: str, range_name: str) -> list:
        """
        Читает значения из указанного диапазона таблицы
        
        Args:
            spreadsheet_id: ID таблицы
            range_name: Диапазон для чтения (например, 'Sheet1!A1:B2')
            
        Returns:
            list: Список списков с прочитанными данными
        """
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            values = result.get('values', [])
            logger.info(f"Данные успешно прочитаны из диапазона {range_name}")
            return values
            
        except Exception as e:
            logger.error(f"Ошибка при чтении данных: {str(e)}")
            raise

    def create_new_sheet(self, spreadsheet_id: str, sheet_name: str) -> int:
        """
        Создает новый лист в указанной таблице с базовым форматированием
        
        Args:
            spreadsheet_id: ID таблицы
            sheet_name: Название нового листа
            
        Returns:
            int: ID созданного листа
        """
        try:
            # Создаем запрос на добавление нового листа
            request_body = {
                'requests': [
                    {
                        'addSheet': {
                            'properties': {
                                'title': sheet_name,
                                # Задаем базовые настройки листа
                                'gridProperties': {
                                    'rowCount': 1000,  # Количество строк
                                    'columnCount': 26,  # Количество столбцов (A-Z)
                                    'frozenRowCount': 1  # Закрепляем первую строку
                                },
                                'tabColor': {  # Цвет вкладки (светло-синий)
                                    'red': 0.8,
                                    'green': 0.9,
                                    'blue': 1.0
                                }
                            }
                        }
                    },
                    # Применяем базовое форматирование к заголовкам
                    {
                        'repeatCell': {
                            'range': {
                                'sheetId': '{{sheetsId}}',  # Будет заменено после создания листа
                                'startRowIndex': 0,
                                'endRowIndex': 1
                            },
                            'cell': {
                                'userEnteredFormat': {
                                    'backgroundColor': {  # Фон заголовков (светло-серый)
                                        'red': 0.95,
                                        'green': 0.95,
                                        'blue': 0.95
                                    },
                                    'textFormat': {
                                        'bold': True,  # Жирный шрифт
                                        'fontSize': 11  # Размер шрифта
                                    },
                                    'horizontalAlignment': 'CENTER',  # Выравнивание по центру
                                    'verticalAlignment': 'MIDDLE'
                                }
                            },
                            'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)'
                        }
                    },
                    # Устанавливаем автоматическую подгонку ширины столбцов
                    {
                        'autoResizeDimensions': {
                            'dimensions': {
                                'sheetId': '{{sheetsId}}',
                                'dimension': 'COLUMNS',
                                'startIndex': 0,
                                'endIndex': 26
                            }
                        }
                    }
                ]
            }
            
            # Выполняем первый запрос для создания листа
            response = self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': [request_body['requests'][0]]}
            ).execute()
            
            # Получаем ID созданного листа
            sheet_id = response['replies'][0]['addSheet']['properties']['sheetId']
            
            # Заменяем placeholder на реальный ID листа
            formatted_requests = []
            for request in request_body['requests'][1:]:
                # Преобразуем запрос в строку для замены
                request_str = str(request)
                # Заменяем placeholder на реальный ID
                request_str = request_str.replace("'{{sheetsId}}'", str(sheet_id))
                # Преобразуем обратно в словарь и добавляем в список
                formatted_requests.append(eval(request_str))
            
            # Выполняем второй запрос для форматирования
            if formatted_requests:
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body={'requests': formatted_requests}
                ).execute()
            
            logger.info(f"Создан новый лист '{sheet_name}' с ID: {sheet_id}")
            return sheet_id
            
        except Exception as e:
            logger.error(f"Ошибка при создании листа: {str(e)}")
            raise

    def copy_sheet_from_template(self, template_id: str, target_spreadsheet_id: str, sheet_name: str = None) -> int:
        """
        Копирует лист из таблицы-шаблона в целевую таблицу
        
        Args:
            template_id: ID таблицы-шаблона
            target_spreadsheet_id: ID целевой таблицы
            sheet_name: Новое имя для скопированного листа (опционально)
            
        Returns:
            int: ID созданного листа
        """
        try:
            # Получаем информацию о первом листе шаблона
            template_metadata = self.service.spreadsheets().get(
                spreadsheetId=template_id
            ).execute()
            source_sheet_id = template_metadata['sheets'][0]['properties']['sheetId']
            
            # Формируем запрос на копирование
            request_body = {
                'destinationSpreadsheetId': target_spreadsheet_id
            }
            
            # Копируем лист
            response = self.service.spreadsheets().sheets().copyTo(
                spreadsheetId=template_id,
                sheetId=source_sheet_id,
                body=request_body
            ).execute()
            
            new_sheet_id = response['sheetId']
            
            # Если указано новое имя, переименовываем лист
            if sheet_name:
                rename_request = {
                    'requests': [{
                        'updateSheetProperties': {
                            'properties': {
                                'sheetId': new_sheet_id,
                                'title': sheet_name
                            },
                            'fields': 'title'
                        }
                    }]
                }
                
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=target_spreadsheet_id,
                    body=rename_request
                ).execute()
            
            logger.info(f"Лист успешно скопирован, новый ID: {new_sheet_id}")
            return new_sheet_id
            
        except Exception as e:
            logger.error(f"Ошибка при копировании листа: {str(e)}")
            raise

    def delete_sheet(self, spreadsheet_id: str, sheet_id: int) -> None:
        """
        Удаляет указанный лист из таблицы
        
        Args:
            spreadsheet_id: ID таблицы
            sheet_id: ID листа для удаления
        """
        try:
            request_body = {
                'requests': [{
                    'deleteSheet': {
                        'sheetId': sheet_id
                    }
                }]
            }
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=request_body
            ).execute()
            
            logger.info(f"Лист с ID {sheet_id} успешно удален")
            
        except Exception as e:
            logger.error(f"Ошибка при удалении листа: {str(e)}")
            raise

    def get_sheets(self, spreadsheet_id: str) -> list:
        """
        Получает список всех листов в таблице
        
        Args:
            spreadsheet_id: ID таблицы
            
        Returns:
            list: Список словарей с информацией о листах
        """
        try:
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            
            sheets = []
            for sheet in spreadsheet['sheets']:
                props = sheet['properties']
                sheets.append({
                    'id': props['sheetId'],
                    'title': props['title'],
                    'index': props['index']
                })
            
            return sheets
            
        except Exception as e:
            logger.error(f"Ошибка при получении списка листов: {str(e)}")
            raise

    def get_sheet_info(self, sheet_id: str) -> Optional[dict]:
        """
        Получает информацию о листе по его ID
        
        Args:
            sheet_id: ID листа (gid)
            
        Returns:
            Optional[dict]: Информация о листе или None, если лист не найден
        """
        try:
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            for sheet in spreadsheet.get('sheets', []):
                if str(sheet['properties']['sheetId']) == str(sheet_id):
                    return sheet['properties']
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при получении информации о листе: {str(e)}")
            return None

    def _get_unique_sheet_name(self, base_name: str) -> str:
        """
        Генерирует уникальное имя листа, добавляя -1, -2 и т.д. если имя занято
        
        Args:
            base_name: Базовое имя листа
            
        Returns:
            str: Уникальное имя листа
        """
        name = base_name
        counter = 1
        
        while True:
            # Проверяем существование листа
            sheets = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute().get('sheets', [])
            
            exists = any(sheet['properties']['title'] == name for sheet in sheets)
            if not exists:
                return name
                
            name = f"{base_name}-{counter}"
            counter += 1

    def create_project_sheet_with_retry(self, project_name: str, sections: List[str]) -> Optional[str]:
        """
        Создает новый лист проекта с заданными разделами.
        
        Args:
            project_name: Название проекта
            sections: Список разделов проекта
            
        Returns:
            Optional[str]: URL созданного листа или None в случае ошибки
        """
        try:
            # Получаем уникальное имя листа
            sheet_name = self._get_unique_sheet_name(project_name)
            
            max_retries = 3
            retry_delay = 2  # секунды
            
            for attempt in range(max_retries):
                try:
                    # Создаем новый лист
                    sheet_metadata = self.service.spreadsheets().get(
                        spreadsheetId=self.spreadsheet_id
                    ).execute()

                    # Получаем следующий доступный индекс для нового листа
                    sheet_count = len(sheet_metadata.get('sheets', []))
                    new_sheet_index = sheet_count

                    # Создаем запрос на добавление листа
                    requests = [{
                        'addSheet': {
                            'properties': {
                                'title': sheet_name,
                                'index': new_sheet_index,
                                'gridProperties': {
                                    'rowCount': 1000,
                                    'columnCount': 26
                                }
                            }
                        }
                    }]

                    # Применяем запрос
                    response = self.service.spreadsheets().batchUpdate(
                        spreadsheetId=self.spreadsheet_id,
                        body={'requests': requests}
                    ).execute()

                    # Получаем ID нового листа
                    new_sheet_id = response['replies'][0]['addSheet']['properties']['sheetId']

                    # Форматируем лист
                    format_requests = [
                        {
                            'updateSheetProperties': {
                                'properties': {
                                    'sheetId': new_sheet_id,
                                    'gridProperties': {
                                        'frozenRowCount': 1
                                    }
                                },
                                'fields': 'gridProperties.frozenRowCount'
                            }
                        },
                        {
                            'repeatCell': {
                                'range': {
                                    'sheetId': new_sheet_id,
                                    'startRowIndex': 0,
                                    'endRowIndex': 1
                                },
                                'cell': {
                                    'userEnteredFormat': {
                                        'backgroundColor': {
                                            'red': 0.95,
                                            'green': 0.95,
                                            'blue': 0.95
                                        },
                                        'textFormat': {
                                            'bold': True
                                        }
                                    }
                                },
                                'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                            }
                        }
                    ]

                    # Записываем заголовки разделов
                    values = [sections]
                    self.service.spreadsheets().values().update(
                        spreadsheetId=self.spreadsheet_id,
                        range=f"{sheet_name}!A1",
                        valueInputOption='RAW',
                        body={'values': values}
                    ).execute()

                    # Применяем форматирование
                    self.service.spreadsheets().batchUpdate(
                        spreadsheetId=self.spreadsheet_id,
                        body={'requests': format_requests}
                    ).execute()
                    
                    # Возвращаем URL листа
                    return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/edit#gid={new_sheet_id}"
                
                except HttpError as e:
                    if e.resp.status == 503 and attempt < max_retries - 1:
                        logger.warning(f"Попытка {attempt + 1} не удалась из-за недоступности сервиса. Ожидание {retry_delay} сек.")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    raise
                    
        except Exception as e:
            logger.error(f"Ошибка при создании листа проекта: {str(e)}")
            raise

if __name__ == "__main__":
    try:
        # Создаем экземпляр класса
        sheets_api = GoogleSheetsAPI()
        
        # Выполняем аутентификацию
        sheets_api.authenticate()
        
        # Тестовые данные проекта
        project_data = {
            "project_name": "Фестиваль ГТО",
            "sections": ["аренда", "судьи", "звук", "свет", "сцена", "сувенирка", "наградная"]
        }
        
        # Создаем лист проекта
        sheet_id = sheets_api.create_project_sheet(project_data)
        print(f"\nСоздан лист проекта с ID: {sheet_id}")
        
        print("\n✅ Все операции выполнены успешно")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {str(e)}")
        logger.critical(f"Критическая ошибка при тестировании: {str(e)}")
