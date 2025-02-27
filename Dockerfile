FROM python:3.9-slim

WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Создаем директорию для логов
RUN mkdir -p /app/logs

# Создаем директорию для credentials, если её нет
RUN mkdir -p /app/credentials

# Открываем порт
EXPOSE 8000

# Запускаем приложение
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
