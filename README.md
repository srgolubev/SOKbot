# Project Sheet Bot

Бот для создания и управления проектными листами в Google Sheets с использованием Telegram и FastAPI.

## Возможности

- Создание проектных листов в Google Sheets на основе шаблонов
- Обработка команд через Telegram бота
- REST API для интеграции с другими системами
- Автоматическое форматирование и расчет сумм в таблицах

## Архитектура

Система развертывается на двух серверах:
1. **Сервер с доменом** (95.163.234.54) - сервер с доменом srgolubev.ru, на котором настроен Nginx для проксирования webhook-запросов
2. **Сервер с ботом** (212.224.118.58) - сервер, на котором запущен бот в Docker-контейнере

Такая архитектура обеспечивает:
- Безопасное SSL-соединение через Nginx
- Разделение ответственности между серверами
- Возможность масштабирования

## Требования

- Python 3.9+
- Docker и Docker Compose (для контейнеризации)
- Доступ к Google Sheets API
- Telegram Bot Token
- Домен с SSL-сертификатом (для webhook)

## Установка и запуск

Подробная инструкция по установке и настройке находится в файле [DEPLOYMENT.md](DEPLOYMENT.md).

### Локальная установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/project-sheet-bot.git
cd project-sheet-bot
```

2. Создайте и активируйте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Настройте переменные окружения в файле `.env`:
```
# Telegram Bot API
TELEGRAM_TOKEN=your_telegram_bot_token
WEBHOOK_URL=https://srgolubev.ru/webhook
WEBHOOK_SECRET=your_webhook_secret

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key
```

5. Настройте учетные данные Google API:
   - Создайте проект в [Google Cloud Console](https://console.cloud.google.com/)
   - Включите Google Sheets API
   - Создайте учетные данные OAuth 2.0
   - Сохраните файл `client_secrets.json` в директорию `credentials/`

6. Запустите приложение:
```bash
python app.py
```

### Запуск в Docker

1. Клонируйте репозиторий и перейдите в директорию проекта

2. Настройте переменные окружения и учетные данные Google API как описано выше

3. Запустите контейнер:
```bash
docker-compose up -d
```

## Структура проекта

- `app.py` - Основной файл FastAPI приложения
- `bot/` - Модули бота
  - `command_processor.py` - Обработка команд
  - `sheets_api.py` - Интеграция с Google Sheets API
  - `telegram_webhook.py` - Обработка Telegram вебхуков
- `tests/` - Тесты
- `credentials/` - Директория для учетных данных Google API
- `Dockerfile` и `docker-compose.yml` - Файлы для контейнеризации
- `nginx/` - Конфигурационные файлы Nginx
- `scripts/` - Вспомогательные скрипты

## Использование

### Команды Telegram бота

Отправьте боту сообщение в формате:
```
Создай таблицу [Название проекта], добавь разделы: [раздел1], [раздел2], ...
```

Например:
```
Создай таблицу Фестиваль Меда, добавь разделы: судьи, сувенирка, наградная
```

### REST API

POST `/webhook` - Принимает сообщения для обработки:
```json
{
  "message": "Создай таблицу Фестиваль Меда, добавь разделы: судьи, сувенирка, наградная"
}
```

GET `/health` - Проверка работоспособности сервиса

## Лицензия

MIT
