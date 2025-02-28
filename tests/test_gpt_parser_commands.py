import pytest
import asyncio
import os
from unittest.mock import patch, MagicMock
from bot.gpt_command_parser import GPTCommandParser, ParsingError
from bot.config import load_config

# Мокаем конфигурацию для тестов
@pytest.fixture
def mock_config():
    """Фикстура для мока конфигурации"""
    with patch('bot.config.load_config', return_value={
        'OPENAI_API_KEY': 'test_key',
        'TELEGRAM_BOT_TOKEN': 'test_token',
        'GOOGLE_SHEETS_ID': 'test_sheet_id',
        'GOOGLE_CREDENTIALS_FILE': 'test_credentials.json'
    }):
        yield

@pytest.fixture
def mock_openai_response():
    """Фикстура для мока ответа от OpenAI"""
    def _create_response(content):
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=content))
        ]
        return mock_response
    return _create_response

@pytest.fixture
def mock_env():
    """Фикстура для мока переменных окружения"""
    with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
        yield

@pytest.fixture
def parser(mock_env, mock_config):
    """Фикстура для создания парсера"""
    return GPTCommandParser()

@pytest.mark.asyncio
async def test_standard_command(parser, mock_openai_response):
    """Тест стандартной команды создания проекта"""
    response = '{"project_name": "Фестиваль ГТО", "sections": ["аренда", "судьи", "звук"], "is_create_table_command": true}'
    
    with patch.object(parser.client.chat.completions, 'create', return_value=mock_openai_response(response)):
        result = await parser.parse_command("Создай проект Фестиваль ГТО с разделами аренда, судьи и звук")
        assert result["project_name"] == "Фестиваль ГТО"
        assert set(result["sections"]) == {"аренда", "судьи", "звук"}
        assert result["is_create_table_command"] == True

@pytest.mark.asyncio
async def test_informal_command(parser, mock_openai_response):
    """Тест неформальной команды"""
    response = '{"project_name": "Кожаный мяч 2027", "sections": ["флаги", "сувенирка", "шатры"], "is_create_table_command": true}'
    
    with patch.object(parser.client.chat.completions, 'create', return_value=mock_openai_response(response)):
        result = await parser.parse_command("У нас новый проект Кожаный мяч 2027. Нужны будут флаги, сувенирка, шатры")
        assert result["project_name"] == "Кожаный мяч 2027"
        assert set(result["sections"]) == {"флаги", "сувенирка", "шатры"}
        assert result["is_create_table_command"] == True

@pytest.mark.asyncio
async def test_project_with_year(parser, mock_openai_response):
    """Тест проекта с годом в названии"""
    response = '{"project_name": "Марафон 2024", "sections": ["регистрация", "питание", "медики"], "is_create_table_command": true}'
    
    with patch.object(parser.client.chat.completions, 'create', return_value=mock_openai_response(response)):
        result = await parser.parse_command("Начинаем проект Марафон 2024, потребуются: регистрация, питание, медики")
        assert result["project_name"] == "Марафон 2024"
        assert set(result["sections"]) == {"регистрация", "питание", "медики"}
        assert result["is_create_table_command"] == True

@pytest.mark.asyncio
async def test_project_without_sections(parser, mock_openai_response):
    """Тест команды без разделов"""
    response = '{"project_name": "Городской праздник", "sections": [], "is_create_table_command": true}'
    
    with patch.object(parser.client.chat.completions, 'create', return_value=mock_openai_response(response)):
        result = await parser.parse_command("Создай проект Городской праздник")
        assert result["project_name"] == "Городской праздник"
        assert result["sections"] == []
        assert result["is_create_table_command"] == True

@pytest.mark.asyncio
async def test_sections_with_colon(parser, mock_openai_response):
    """Тест команды с двоеточием перед разделами"""
    response = '{"project_name": "День города", "sections": ["сцена", "свет", "звук"], "is_create_table_command": true}'
    
    with patch.object(parser.client.chat.completions, 'create', return_value=mock_openai_response(response)):
        result = await parser.parse_command("Нужна таблица для проекта День города: сцена, свет, звук")
        assert result["project_name"] == "День города"
        assert set(result["sections"]) == {"сцена", "свет", "звук"}
        assert result["is_create_table_command"] == True

@pytest.mark.asyncio
async def test_invalid_command(parser):
    """Тест некорректной команды"""
    with pytest.raises(ParsingError):
        await parser.parse_command("")

@pytest.mark.asyncio
async def test_invalid_gpt_response(parser, mock_openai_response):
    """Тест некорректного ответа от GPT"""
    response = '{"invalid": "response"}'
    
    with patch.object(parser.client.chat.completions, 'create', return_value=mock_openai_response(response)):
        with pytest.raises(ParsingError):
            await parser.parse_command("Создай проект Тест")

if __name__ == "__main__":
    pytest.main([__file__])
