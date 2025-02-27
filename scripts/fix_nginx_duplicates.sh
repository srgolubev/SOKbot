#!/bin/bash

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверяем root права
if [ "$EUID" -ne 0 ]; then
    error "Этот скрипт должен быть запущен с правами root"
    exit 1
fi

log "Начинаем исправление дубликатов в конфигурации Nginx..."

# Создаем резервные копии
log "Создаем резервные копии..."
cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.bak
cp -r /etc/nginx/sites-available /etc/nginx/sites-available.bak

# Очищаем sites-enabled
log "Очищаем директорию sites-enabled..."
rm -f /etc/nginx/sites-enabled/*

# Создаем базовую конфигурацию nginx.conf
log "Создаем базовую конфигурацию nginx.conf..."
cat > /etc/nginx/nginx.conf << 'EOF'
user www-data;
worker_processes auto;
pid /run/nginx.pid;
include /etc/nginx/modules-enabled/*.conf;

events {
    worker_connections 768;
}

http {
    sendfile on;
    tcp_nopush on;
    types_hash_max_size 2048;
    server_tokens off;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    gzip on;

    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
EOF

# Создаем единую конфигурацию для домена
log "Создаем конфигурацию для домена..."
cat > /etc/nginx/sites-available/telegram-bot.conf << 'EOF'
# HTTP -> HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name srgolubev.ru;
    
    location / {
        return 301 https://$host$request_uri;
    }
}

# Main HTTPS server
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name srgolubev.ru;

    ssl_certificate /etc/letsencrypt/live/srgolubev.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/srgolubev.ru/privkey.pem;

    root /opt/SOKbot/public;
    index index.html;

    # Основной маршрут для статических файлов
    location / {
        try_files $uri $uri/ =404;
        add_header Content-Type $content_type;
    }

    # Проксирование запросов к вебхуку
    location /webhook {
        proxy_pass http://212.224.118.58:8000/webhook;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /webhook/telegram {
        proxy_pass http://212.224.118.58:8000/webhook/telegram;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://212.224.118.58:8000/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Создаем символическую ссылку
log "Создаем символическую ссылку..."
ln -s /etc/nginx/sites-available/telegram-bot.conf /etc/nginx/sites-enabled/

# Проверяем конфигурацию
log "Проверяем конфигурацию..."
nginx -t

if [ $? -eq 0 ]; then
    log "Конфигурация корректна. Перезапускаем Nginx..."
    systemctl restart nginx
    
    if systemctl is-active --quiet nginx; then
        log "Nginx успешно перезапущен"
        log "Проверьте работу сайта: https://srgolubev.ru"
    else
        error "Ошибка при перезапуске Nginx"
        systemctl status nginx
    fi
else
    error "Ошибка в конфигурации. Восстанавливаем из резервной копии..."
    cp /etc/nginx/nginx.conf.bak /etc/nginx/nginx.conf
    cp -r /etc/nginx/sites-available.bak/* /etc/nginx/sites-available/
    systemctl restart nginx
fi
