import pytest
from unittest.mock import patch

@pytest.fixture(autouse=True)
def mock_config():
    """Автоматически подменяем конфигурацию во всех тестах"""
    config = {
        "OPENAI_API_KEY": "test-key",
        "TELEGRAM_BOT_TOKEN": "test-token",
        "GOOGLE_SHEETS_ID": "test-sheet-id",
        "GOOGLE_CREDENTIALS_FILE": "test-credentials.json"
    }
    with patch('bot.command_processor.load_config', return_value=config), \
         patch('bot.sheets_api.load_config', return_value=config):
        yield config
