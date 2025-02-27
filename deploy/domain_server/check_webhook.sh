#!/bin/bash
# Скрипт для проверки статуса вебхука Telegram бота

# Загружаем переменные окружения из .env файла
if [ -f ../.env ]; then
    source ../.env
else
    echo "Файл .env не найден. Пожалуйста, создайте его с переменной TELEGRAM_TOKEN."
    exit 1
fi

# Проверяем, что TELEGRAM_TOKEN установлен
if [ -z "$TELEGRAM_TOKEN" ]; then
    echo "TELEGRAM_TOKEN не найден в переменных окружения."
    exit 1
fi

# Получаем информацию о вебхуке
echo "Получаем информацию о вебхуке для бота..."
curl -s "https://api.telegram.org/bot$TELEGRAM_TOKEN/getWebhookInfo" | jq .

# Проверяем доступность вебхука
if [ ! -z "$WEBHOOK_URL" ]; then
    echo -e "\nПроверяем доступность вебхука по URL: $WEBHOOK_URL"
    curl -s -I "$WEBHOOK_URL" | head -n 1
    
    # Проверяем /webhook/telegram эндпоинт
    echo -e "\nПроверяем доступность /webhook/telegram эндпоинта:"
    curl -s -I "${WEBHOOK_URL}/telegram" | head -n 1
else
    echo "WEBHOOK_URL не найден в переменных окружения."
fi

# Проверяем статус сервера с ботом
echo -e "\nПроверяем доступность сервера с ботом (212.224.118.58):"
ping -c 3 212.224.118.58 | grep "time="

# Проверяем статус сервера с доменом
echo -e "\nПроверяем доступность сервера с доменом (95.163.234.54):"
ping -c 3 95.163.234.54 | grep "time="

echo -e "\nПроверка завершена."
