import os
import pytest
from bot.sheets_api import GoogleSheetsAPI

# Установите переменные окружения для тестирования
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'path/to/your/credentials.json'

@pytest.fixture
def sheets_api():
    api = GoogleSheetsAPI()
    api.authenticate()
    return api


def test_create_spreadsheet(sheets_api):
    spreadsheet_id = sheets_api.create_spreadsheet('Test Spreadsheet')
    assert spreadsheet_id is not None


def test_create_new_sheet(sheets_api):
    spreadsheet_id = sheets_api.create_spreadsheet('Test Spreadsheet')
    sheet_id = sheets_api.create_new_sheet(spreadsheet_id, 'Test Sheet')
    assert sheet_id is not None


def test_write_and_read_values(sheets_api):
    spreadsheet_id = sheets_api.create_spreadsheet('Test Spreadsheet')
    sheet_id = sheets_api.create_new_sheet(spreadsheet_id, 'Test Sheet')
    range_name = 'A1:B2'
    values = [["Hello", "World"], ["1", "2"]]
    sheets_api.write_values(spreadsheet_id, range_name, values)
    read_values = sheets_api.read_values(spreadsheet_id, range_name)
    assert read_values == values
