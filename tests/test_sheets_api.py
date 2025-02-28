import pytest
from unittest.mock import Mock, patch, AsyncMock
from bot.sheets_api import GoogleSheetsAPI

@pytest.fixture
def mock_config():
    return {
        "GOOGLE_SHEETS_ID": "test-sheet-id",
        "GOOGLE_CREDENTIALS_FILE": "test-credentials.json"
    }

@pytest.fixture
def mock_sheets_service():
    mock_service = Mock()
    mock_service.spreadsheets().get().execute.return_value = {
        'sheets': [
            {'properties': {'title': 'Существующий проект', 'sheetId': '123'}},
            {'properties': {'title': 'Другой проект', 'sheetId': '456'}}
        ]
    }
    return mock_service

@pytest.fixture
def mock_sheets_api(mock_config):
    with patch('bot.sheets_api.load_config', return_value=mock_config), \
         patch('google.oauth2.service_account.Credentials.from_service_account_file'):
        api = GoogleSheetsAPI()
        api.spreadsheet_id = 'test_spreadsheet_id'
        return api

def test_get_unique_sheet_name(mock_sheets_service, mock_sheets_api):
    """Тест генерации уникального имени листа"""
    with patch.object(mock_sheets_api, 'service', mock_sheets_service):
        # Тест 1: Имя свободно
        name = mock_sheets_api._get_unique_sheet_name("Новый проект")
        assert name == "Новый проект"
        
        # Тест 2: Имя занято
        name = mock_sheets_api._get_unique_sheet_name("Существующий проект")
        assert name == "Существующий проект-1"
        
        # Тест 3: Имя с суффиксом тоже занято
        mock_sheets_service.spreadsheets().get().execute.return_value = {
            'sheets': [
                {'properties': {'title': 'Тест', 'sheetId': '123'}},
                {'properties': {'title': 'Тест-1', 'sheetId': '456'}}
            ]
        }
        name = mock_sheets_api._get_unique_sheet_name("Тест")
        assert name == "Тест-2"

def test_get_sheet_info(mock_sheets_service, mock_sheets_api):
    """Тест получения информации о листе по ID"""
    with patch.object(mock_sheets_api, 'service', mock_sheets_service):
        # Тест 1: Лист существует
        info = mock_sheets_api.get_sheet_info('123')
        assert info['title'] == 'Существующий проект'
        
        # Тест 2: Лист не существует
        info = mock_sheets_api.get_sheet_info('999')
        assert info is None

@pytest.mark.asyncio
async def test_create_project_sheet_with_retry(mock_sheets_api):
    """Тест создания листа проекта с повторными попытками"""
    mock_service = Mock()
    
    # Настраиваем мок для успешного создания листа
    mock_service.spreadsheets().get().execute.return_value = {'sheets': []}
    mock_service.spreadsheets().batchUpdate().execute.return_value = {
        'replies': [{'addSheet': {'properties': {'sheetId': '789'}}}]
    }
    mock_service.spreadsheets().values().update().execute = AsyncMock()
    
    with patch.object(mock_sheets_api, 'service', mock_service):
        # Тест успешного создания
        url = await mock_sheets_api.create_project_sheet_with_retry(
            "Новый проект",
            ["Раздел 1", "Раздел 2"]
        )
        assert url is not None
        assert "789" in url
        
        # Проверяем вызовы методов
        mock_service.spreadsheets().batchUpdate.assert_called_once()
        mock_service.spreadsheets().values().update.assert_called()

@pytest.mark.asyncio
async def test_create_project_sheet_error_handling(mock_sheets_api):
    """Тест обработки ошибок при создании листа"""
    mock_service = Mock()
    mock_service.spreadsheets().batchUpdate.side_effect = Exception("Service error")
    
    with patch.object(mock_sheets_api, 'service', mock_service), \
         pytest.raises(Exception) as exc_info:
        await mock_sheets_api.create_project_sheet_with_retry(
            "Проблемный проект",
            ["Раздел 1"]
        )
    assert "Service error" in str(exc_info.value)
