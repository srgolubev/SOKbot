#!/bin/bash
# Скрипт для исправления проблем на сервере с доменом

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверяем, запущен ли скрипт с правами root
if [ "$EUID" -ne 0 ]; then
    error "Этот скрипт должен быть запущен с правами root"
    exit 1
fi

# Переходим в директорию проекта
cd /opt/SOKbot || exit 1

log "Начинаем исправление проблем на сервере с доменом (95.163.234.54)..."

# Проверяем наличие директории public
if [ ! -d "/opt/SOKbot/public" ]; then
    log "Создаем директорию public..."
    mkdir -p /opt/SOKbot/public
fi

# Проверяем наличие файла index.html
if [ ! -f "/opt/SOKbot/public/index.html" ]; then
    error "Файл index.html не найден в директории public"
    log "Копируем файл index.html из репозитория..."
    cp -f /opt/SOKbot/public/index.html /opt/SOKbot/public/
fi

# Устанавливаем правильные права доступа
log "Устанавливаем правильные права доступа..."
chown -R www-data:www-data /opt/SOKbot/public
chmod -R 755 /opt/SOKbot/public

# Проверяем конфигурацию Nginx
log "Проверяем конфигурацию Nginx..."
cat /etc/nginx/sites-available/telegram-bot.conf

# Обновляем конфигурацию Nginx для обработки статических файлов
log "Обновляем конфигурацию Nginx..."
cat > /etc/nginx/sites-available/telegram-bot.conf << 'EOF'
server {
    listen 80;
    server_name srgolubev.ru;

    # Перенаправление HTTP на HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name srgolubev.ru;

    # SSL-сертификаты
    ssl_certificate /etc/letsencrypt/live/srgolubev.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/srgolubev.ru/privkey.pem;

    # Оптимизация SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;

    # Корневая директория для статических файлов
    root /opt/SOKbot/public;
    index index.html;

    # Основной маршрут для статических файлов
    location / {
        try_files $uri $uri/ /index.html;
        add_header Content-Type text/html;
    }

    # Проксирование запросов к вебхуку на сервер с ботом
    location /webhook {
        proxy_pass http://212.224.118.58:8000/webhook;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Проксирование запросов к вебхуку Telegram на сервер с ботом
    location /webhook/telegram {
        proxy_pass http://212.224.118.58:8000/webhook/telegram;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Проксирование запросов к эндпоинту проверки здоровья на сервер с ботом
    location /health {
        proxy_pass http://212.224.118.58:8000/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Проверяем конфигурацию Nginx
log "Проверяем обновленную конфигурацию Nginx..."
nginx -t
if [ $? -ne 0 ]; then
    error "Ошибка в конфигурации Nginx."
    exit 1
fi

# Перезапускаем Nginx
log "Перезапускаем Nginx..."
systemctl restart nginx

# Проверяем содержимое директории public
log "Проверяем содержимое директории public..."
ls -la /opt/SOKbot/public

# Проверяем доступность домена
log "Проверяем доступность домена..."
curl -v https://srgolubev.ru

log "Исправление проблем на сервере с доменом завершено!"
