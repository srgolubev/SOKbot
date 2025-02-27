@echo off
REM Создаем директорию для логов, если её нет
if not exist logs mkdir logs

REM Запускаем приложение
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
