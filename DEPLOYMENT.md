# Инструкция по развертыванию на двух серверах

## Архитектура

Система состоит из двух серверов:
1. **Сервер с доменом** (далее "Сервер 1") - сервер с доменом srgolubev.ru (IP: 95.163.234.54), на котором настроен Nginx для проксирования webhook-запросов
2. **Сервер с ботом** (далее "Сервер 2") - сервер с IP-адресом 212.224.118.58, на котором запущен бот в Docker-контейнере

## Настройка Сервера 1 (с доменом)

1. **Установите Nginx**:
   ```bash
   sudo apt update
   sudo apt install nginx
   ```

2. **Настройте SSL-сертификат** с помощью Let's Encrypt:
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d srgolubev.ru
   ```

3. **Скопируйте конфигурацию Nginx**:
   ```bash
   sudo cp nginx/telegram-bot.conf /etc/nginx/sites-available/
   sudo ln -s /etc/nginx/sites-available/telegram-bot.conf /etc/nginx/sites-enabled/
   ```

4. **Проверьте конфигурацию и перезапустите Nginx**:
   ```bash
   sudo nginx -t
   sudo systemctl restart nginx
   ```

## Настройка Сервера 2 (с ботом)

1. **Клонируйте репозиторий**:
   ```bash
   git clone https://github.com/yourusername/project-sheet-bot.git
   cd project-sheet-bot
   ```

2. **Создайте файл .env**:
   ```bash
   cat > .env << 'EOF'
   # Telegram Bot API
   TELEGRAM_TOKEN=7613482703:AAEqKQXFZi1EOFtzrT_83J9lGgAtwVTThQM
   WEBHOOK_URL=https://srgolubev.ru/webhook
   WEBHOOK_SECRET=0ab6399b169d0413a0eb3f2d0c1024f04d2859eb6ace07c9e49864f6860ce0d0

   # OpenAI API Key
   OPENAI_API_KEY=sk-***********************************
   EOF
   ```

3. **Создайте директорию для учетных данных Google API**:
   ```bash
   mkdir -p credentials
   ```

4. **Скопируйте файл client_secrets.json** в директорию credentials:
   ```bash
   # Скопируйте файл с локального компьютера или создайте новый
   nano credentials/client_secrets.json
   ```

5. **Настройте брандмауэр**, чтобы разрешить входящие соединения на порт 8000 с IP-адреса Сервера 1:
   ```bash
   sudo ufw allow from 95.163.234.54 to any port 8000
   ```

6. **Запустите приложение в Docker**:
   ```bash
   docker-compose up -d
   ```

7. **Проверьте логи**:
   ```bash
   docker-compose logs -f
   ```

## Проверка работоспособности

1. **Проверьте доступность webhook URL**:
   ```bash
   curl -k https://srgolubev.ru/status
   ```
   Должен вернуться статус 200 и сообщение "Telegram Bot Webhook is operational".

2. **Проверьте настройку вебхука в Telegram**:
   ```bash
   curl -X GET "https://api.telegram.org/bot7613482703:AAEqKQXFZi1EOFtzrT_83J9lGgAtwVTThQM/getWebhookInfo"
   ```
   В ответе должен быть указан URL `https://srgolubev.ru/webhook`.

3. **Отправьте тестовое сообщение боту** и проверьте логи на Сервере 2:
   ```bash
   docker-compose logs -f
   ```

## Обновление приложения

Для обновления приложения на Сервере 2:

1. **Получите последние изменения**:
   ```bash
   git pull
   ```

2. **Пересоберите и перезапустите контейнер**:
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

## Устранение неполадок

1. **Проверьте логи Nginx** на Сервере 1:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   sudo tail -f /var/log/nginx/access.log
   ```

2. **Проверьте логи приложения** на Сервере 2:
   ```bash
   docker-compose logs -f
   ```

3. **Проверьте статус контейнера**:
   ```bash
   docker-compose ps
   ```

4. **Проверьте сетевую доступность** между серверами:
   ```bash
   # На Сервере 1
   telnet 212.224.118.58 8000
   ```
