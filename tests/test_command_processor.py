import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from bot.command_processor import CommandProcessor

@pytest.fixture
def mock_openai_client():
    mock_client = Mock()
    mock_client.chat.completions.create = AsyncMock(return_value=Mock(
        choices=[Mock(message=Mock(content=json.dumps({
            "project_name": "Тестовый проект",
            "sections": ["организация", "техника", "персонал"]
        })))]
    ))
    return mock_client

@pytest.fixture
def mock_telegram_message():
    return {
        "message_id": 80,
        "from": {
            "id": 2462754,
            "is_bot": False,
            "first_name": "Serg",
            "username": "srgolubev"
        },
        "chat": {
            "id": 2462754,
            "type": "private"
        },
        "date": 1740700549,
        "text": 'Создай проект "Тестовый проект" с разделами организация, техника, персонал'
    }

@pytest.fixture
def mock_config():
    return {
        "OPENAI_API_KEY": "test-key",
        "TELEGRAM_BOT_TOKEN": "test-token",
        "GOOGLE_SHEETS_ID": "test-sheet-id"
    }

@pytest.mark.asyncio
async def test_extract_project_info(mock_openai_client, mock_config):
    """Тест извлечения информации о проекте из сообщения"""
    with patch('openai.OpenAI', return_value=mock_openai_client), \
         patch('bot.command_processor.load_config', return_value=mock_config):
        processor = CommandProcessor()
        result = await processor._extract_project_info(
            'Создай проект "Тестовый проект" с разделами организация, техника, персонал'
        )
        
        assert result["project_name"] == "Тестовый проект"
        assert result["sections"] == ["организация", "техника", "персонал"]
        
        # Проверяем, что был вызван правильный метод OpenAI с JSON форматом
        mock_openai_client.chat.completions.create.assert_called_once()
        args = mock_openai_client.chat.completions.create.call_args[1]
        assert args["response_format"]["type"] == "json_object"

@pytest.mark.asyncio
async def test_process_command(mock_openai_client, mock_config):
    """Тест обработки команды создания проекта"""
    with patch('openai.OpenAI', return_value=mock_openai_client), \
         patch('bot.command_processor.load_config', return_value=mock_config), \
         patch('bot.sheets_api.GoogleSheetsAPI.create_project_sheet_with_retry') as mock_create_sheet, \
         patch('telegram.Bot.send_message') as mock_send:
        
        # Настраиваем моки
        mock_create_sheet.return_value = "https://docs.google.com/spreadsheets/d/xxx/edit#gid=123"
        mock_send = AsyncMock()
        
        processor = CommandProcessor()
        await processor.process_command(
            chat_id=2462754,
            command='Создай проект "Тестовый проект" с разделами организация, техника, персонал'
        )
        
        # Проверяем, что методы были вызваны с правильными параметрами
        mock_openai_client.chat.completions.create.assert_called_once()
        mock_create_sheet.assert_called_once_with(
            "Тестовый проект",
            ["организация", "техника", "персонал"]
        )

@pytest.mark.asyncio
async def test_process_command_duplicate_name(mock_openai_client, mock_config):
    """Тест обработки случая, когда лист с таким именем уже существует"""
    with patch('openai.OpenAI', return_value=mock_openai_client), \
         patch('bot.command_processor.load_config', return_value=mock_config), \
         patch('bot.sheets_api.GoogleSheetsAPI.create_project_sheet_with_retry') as mock_create_sheet, \
         patch('telegram.Bot.send_message') as mock_send:
        
        # Возвращаем URL с измененным именем (добавлен "-1")
        mock_create_sheet.return_value = "https://docs.google.com/spreadsheets/d/xxx/edit#gid=123"
        mock_send = AsyncMock()
        
        processor = CommandProcessor()
        await processor.process_command(
            chat_id=2462754,
            command='Создай проект "Тестовый проект" с разделами организация, техника, персонал'
        )
        
        # Проверяем, что методы были вызваны
        mock_openai_client.chat.completions.create.assert_called_once()
        mock_create_sheet.assert_called_once()

@pytest.mark.asyncio
async def test_process_command_extraction_failed(mock_config):
    """Тест обработки ошибки при извлечении информации о проекте"""
    with patch('openai.OpenAI') as mock_openai, \
         patch('bot.command_processor.load_config', return_value=mock_config), \
         patch('telegram.Bot.send_message') as mock_send:
        
        # Настраиваем мок для ошибки
        mock_client = Mock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
        mock_openai.return_value = mock_client
        mock_send = AsyncMock()
        
        processor = CommandProcessor()
        await processor.process_command(
            chat_id=2462754,
            command='Неправильный формат команды'
        )
        
        # Проверяем, что отправлено сообщение об ошибке
        mock_client.chat.completions.create.assert_called_once()
        assert mock_send.call_count == 1  # Должно быть отправлено сообщение об ошибке
