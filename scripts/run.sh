#!/bin/bash

# Создаем директорию для логов, если её нет
mkdir -p logs

# Запускаем приложение
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
