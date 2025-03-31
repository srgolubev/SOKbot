import os
import pytest
from unittest.mock import MagicMock, patch
from bot.sheets_api import GoogleSheetsAPI

@pytest.fixture
def mock_sheets_api():
    """
    Создает мок объект GoogleSheetsAPI для тестирования без реальной аутентификации.
    """
    with patch('google.oauth2.service_account.Credentials.from_service_account_file'), \
         patch('googleapiclient.discovery.build'), \
         patch('os.path.exists', return_value=True):
        
        api = GoogleSheetsAPI()
        
        # Мокаем сервисный объект
        api.service = MagicMock()
        
        # Мокаем метод execute для spreadsheets().create()
        spreadsheet_create = MagicMock()
        spreadsheet_create.execute.return_value = {'spreadsheetId': 'test_spreadsheet_id'}
        api.service.spreadsheets().create.return_value = spreadsheet_create
        
        # Мокаем метод execute для spreadsheets().batchUpdate()
        batch_update = MagicMock()
        batch_update.execute.return_value = {
            'replies': [{'addSheet': {'properties': {'sheetId': 123}}}]
        }
        api.service.spreadsheets().batchUpdate.return_value = batch_update
        
        # Мокаем метод execute для spreadsheets().values().update()
        values_update = MagicMock()
        values_update.execute.return_value = {'updatedCells': 4}
        api.service.spreadsheets().values().update.return_value = values_update
        
        # Мокаем метод execute для spreadsheets().values().get()
        values_get = MagicMock()
        values_get.execute.return_value = {'values': [["Hello", "World"], ["1", "2"]]}
        api.service.spreadsheets().values().get.return_value = values_get
        
        return api


def test_create_spreadsheet(mock_sheets_api):
    """
    Тестирует создание новой таблицы Google Sheets.
    """
    spreadsheet_id = mock_sheets_api.create_spreadsheet('Test Spreadsheet')
    assert spreadsheet_id == 'test_spreadsheet_id'
    mock_sheets_api.service.spreadsheets().create.assert_called_once()


def test_create_new_sheet(mock_sheets_api):
    """
    Тестирует создание нового листа в таблице Google Sheets.
    """
    sheet_id = mock_sheets_api.create_new_sheet('test_spreadsheet_id', 'Test Sheet')
    assert sheet_id == 123
    mock_sheets_api.service.spreadsheets().batchUpdate.assert_called()


def test_write_values(mock_sheets_api):
    """
    Тестирует запись значений в таблицу Google Sheets.
    """
    range_name = 'A1:B2'
    values = [["Hello", "World"], ["1", "2"]]
    mock_sheets_api.write_values('test_spreadsheet_id', range_name, values)
    mock_sheets_api.service.spreadsheets().values().update.assert_called_once()


def test_read_values(mock_sheets_api):
    """
    Тестирует чтение значений из таблицы Google Sheets.
    """
    range_name = 'A1:B2'
    expected_values = [["Hello", "World"], ["1", "2"]]
    values = mock_sheets_api.read_values('test_spreadsheet_id', range_name)
    assert values == expected_values
    mock_sheets_api.service.spreadsheets().values().get.assert_called_once()
