import os
import json
import logging
from typing import Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

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
        
        # Путь к файлу с секретами клиента
        self.client_secrets_file = os.path.join('credentials', 'client_secrets.json')
        if not os.path.exists(self.client_secrets_file):
            raise FileNotFoundError(f"Файл {self.client_secrets_file} не найден")

    def _save_credentials(self, credentials: Credentials) -> None:
        """
        Сохраняет учетные данные в файл token.json
        
        Args:
            credentials: Объект с учетными данными
        """
        try:
            # Создаем директорию для токена, если её нет
            os.makedirs('credentials', exist_ok=True)
            
            # Сохраняем токен
            token_path = os.path.join('credentials', 'token.json')
            with open(token_path, 'w') as token:
                token.write(credentials.to_json())
                
            logger.info("Учетные данные успешно сохранены")
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении учетных данных: {str(e)}")
            raise

    def _load_credentials(self) -> Optional[Credentials]:
        """
        Загружает сохраненные учетные данные из файла token.json
        
        Returns:
            Optional[Credentials]: Объект с учетными данными или None, если файл не найден
        """
        try:
            token_path = os.path.join('credentials', 'token.json')
            if os.path.exists(token_path):
                with open(token_path, 'r') as token:
                    creds_data = json.load(token)
                    credentials = Credentials.from_authorized_user_info(creds_data, SCOPES)
                    logger.info("Учетные данные успешно загружены")
                    return credentials
                    
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке учетных данных: {str(e)}")
            return None

    def authenticate(self) -> None:
        """
        Выполняет аутентификацию с Google Sheets API
        
        Процесс аутентификации:
        1. Пытается загрузить существующие учетные данные
        2. Проверяет, действительны ли они
        3. Если нет - запускает процесс OAuth 2.0
        4. Сохраняет новые учетные данные
        5. Создает сервисный объект для работы с API
        
        Raises:
            Exception: Если произошла ошибка при аутентификации
        """
        try:
            # Пытаемся загрузить существующие учетные данные
            self.credentials = self._load_credentials()
            
            # Если учетные данные есть и они валидны
            if self.credentials and self.credentials.valid:
                if self.credentials.expired and self.credentials.refresh_token:
                    # Обновляем токен, если он истек
                    self.credentials.refresh(Request())
                    logger.info("Токен успешно обновлен")
            else:
                # Запускаем процесс OAuth 2.0
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_file, 
                    SCOPES,
                    redirect_uri='urn:ietf:wg:oauth:2.0:oob'
                )
                self.credentials = flow.run_local_server(port=0)
                logger.info("Получены новые учетные данные через OAuth 2.0")
                
                # Сохраняем учетные данные
                self._save_credentials(self.credentials)
            
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

    def _get_unique_sheet_name(self, spreadsheet_id: str, base_name: str) -> str:
        """
        Генерирует уникальное имя листа, добавляя '-1', '-2' и т.д. если имя уже существует
        
        Args:
            spreadsheet_id: ID таблицы
            base_name: Базовое имя листа
            
        Returns:
            str: Уникальное имя листа
        """
        # Получаем список существующих листов
        spreadsheet = self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        existing_names = [sheet['properties']['title'] for sheet in spreadsheet['sheets']]
        
        # Если базовое имя не существует, возвращаем его
        if base_name not in existing_names:
            return base_name
        
        # Иначе добавляем числовой суффикс
        counter = 1
        while f"{base_name}-{counter}" in existing_names:
            counter += 1
        
        return f"{base_name}-{counter}"

    def create_project_sheet_with_retry(self, project_name: str, sections: List[str]) -> int:
        """
        Создает новый лист проекта с заданными разделами на основе шаблонов.
        
        Args:
            project_name: Название проекта
            sections: Список разделов проекта
            
        Returns:
            int: ID созданного листа
        """
        # Создаем словарь с данными проекта
        project_data = {
            "project_name": project_name,
            "sections": sections
        }
        
        # Вызываем основной метод создания листа
        return self.create_project_sheet(project_data)
    
    def create_project_sheet(self, project_data: dict) -> int:
        """
        Создает новый лист проекта на основе шаблонов
        
        Args:
            project_data: Словарь с данными проекта вида:
                {
                    "project_name": "Название проекта",
                    "sections": ["секция1", "секция2", ...]
                }
            
        Returns:
            int: ID созданного листа
        """
        try:
            # Загружаем конфигурацию
            with open('credentials/client_secrets.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            main_sheet_id = config['installed']['main_sheet']
            template_top_id = config['installed']['template_top']
            template_section_id = config['installed']['template_section']
            
            # Получаем уникальное имя листа
            sheet_name = self._get_unique_sheet_name(main_sheet_id, project_data['project_name'])
            
            # Копируем шаблон верхней части в основную таблицу
            template_metadata = self.service.spreadsheets().get(
                spreadsheetId=template_top_id
            ).execute()
            source_sheet_id = template_metadata['sheets'][0]['properties']['sheetId']
            
            # Копируем лист с форматированием
            request_body = {
                'destinationSpreadsheetId': main_sheet_id
            }
            
            response = self.service.spreadsheets().sheets().copyTo(
                spreadsheetId=template_top_id,
                sheetId=source_sheet_id,
                body=request_body
            ).execute()
            
            new_sheet_id = response['sheetId']
            
            # Переименовываем лист
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
                spreadsheetId=main_sheet_id,
                body=rename_request
            ).execute()
            
            # Получаем текущее количество строк в шаблоне верхней части
            top_values = self.read_values(template_top_id, 'A1:A')
            current_row = len(top_values) + 1 if top_values else 4
            
            # Сохраняем начальную строку для формулы
            formula_parts = []
            
            # Для каждой секции копируем шаблон и заменяем placeholder
            all_sections = project_data['sections'] + ['Прочее']  # Добавляем секцию "Прочее" с заглавной буквы
            
            for section in all_sections:
                # Добавляем ссылку на ячейку с суммой для текущей секции
                formula_parts.append(f'E{current_row}')
                
                # Получаем данные из шаблона секции
                section_metadata = self.service.spreadsheets().get(
                    spreadsheetId=template_section_id
                ).execute()
                section_sheet_id = section_metadata['sheets'][0]['properties']['sheetId']
                
                # Копируем секцию во временный лист
                temp_response = self.service.spreadsheets().sheets().copyTo(
                    spreadsheetId=template_section_id,
                    sheetId=section_sheet_id,
                    body={'destinationSpreadsheetId': main_sheet_id}
                ).execute()
                
                temp_sheet_id = temp_response['sheetId']
                temp_sheet_title = temp_response['title']
                
                # Читаем данные из временного листа
                section_values = self.read_values(main_sheet_id, f'{temp_sheet_title}!A1:J')
                
                if section_values:
                    # Получаем информацию о ячейках, включая формулы
                    sheet_data = self.service.spreadsheets().get(
                        spreadsheetId=main_sheet_id,
                        ranges=[f'{temp_sheet_title}!A1:J'],
                        includeGridData=True
                    ).execute()
                    
                    grid_data = sheet_data['sheets'][0]['data'][0]['rowData']
                    
                    # Собираем обновления для текстовых ячеек
                    requests = []
                    for row_idx, row in enumerate(grid_data):
                        if 'values' in row:
                            for col_idx, cell in enumerate(row['values']):
                                # Проверяем, что это текстовая ячейка без формулы
                                if ('userEnteredValue' in cell and 
                                    'stringValue' in cell['userEnteredValue'] and 
                                    '{sectionName}' in cell['userEnteredValue']['stringValue']):
                                    
                                    requests.append({
                                        'updateCells': {
                                            'range': {
                                                'sheetId': new_sheet_id,
                                                'startRowIndex': current_row - 1 + row_idx,
                                                'endRowIndex': current_row + row_idx,
                                                'startColumnIndex': col_idx,
                                                'endColumnIndex': col_idx + 1
                                            },
                                            'rows': [{
                                                'values': [{
                                                    'userEnteredValue': {
                                                        'stringValue': cell['userEnteredValue']['stringValue'].replace('{sectionName}', section.title())
                                                    }
                                                }]
                                            }],
                                            'fields': 'userEnteredValue'
                                        }
                                    })
                    
                    # Копируем секцию целиком
                    copy_request = {
                        'requests': [
                            {
                                'copyPaste': {
                                    'source': {
                                        'sheetId': temp_sheet_id,
                                        'startRowIndex': 0,
                                        'endRowIndex': len(section_values),
                                        'startColumnIndex': 0,
                                        'endColumnIndex': 10  # Явно указываем 10 столбцов
                                    },
                                    'destination': {
                                        'sheetId': new_sheet_id,
                                        'startRowIndex': current_row - 1,
                                        'endRowIndex': current_row - 1 + len(section_values),
                                        'startColumnIndex': 0,
                                        'endColumnIndex': 10  # Явно указываем 10 столбцов
                                    },
                                    'pasteType': 'PASTE_NORMAL'
                                }
                            }
                        ]
                    }
                    
                    # Применяем копирование
                    self.service.spreadsheets().batchUpdate(
                        spreadsheetId=main_sheet_id,
                        body=copy_request
                    ).execute()
                    
                    # Применяем обновления текстовых ячеек
                    if requests:
                        update_request = {'requests': requests}
                        self.service.spreadsheets().batchUpdate(
                            spreadsheetId=main_sheet_id,
                            body=update_request
                        ).execute()
                    
                    # Обновляем текущую строку
                    current_row += len(section_values)
                
                # Удаляем временный лист
                delete_request = {
                    'requests': [{
                        'deleteSheet': {
                            'sheetId': temp_sheet_id
                        }
                    }]
                }
                
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=main_sheet_id,
                    body=delete_request
                ).execute()
            
            # Обновляем формулу суммы в ячейке E2
            formula = '=' + '+'.join(formula_parts)
            formula_request = {
                'requests': [{
                    'updateCells': {
                        'range': {
                            'sheetId': new_sheet_id,
                            'startRowIndex': 1,
                            'endRowIndex': 2,
                            'startColumnIndex': 4,
                            'endColumnIndex': 5
                        },
                        'rows': [{
                            'values': [{
                                'userEnteredValue': {
                                    'formulaValue': formula
                                }
                            }]
                        }],
                        'fields': 'userEnteredValue'
                    }
                }]
            }
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=main_sheet_id,
                body=formula_request
            ).execute()
            
            logger.info(f"Создан лист проекта '{project_data['project_name']}' с ID: {new_sheet_id}")
            return new_sheet_id
            
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
