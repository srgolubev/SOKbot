#!/bin/bash
# Скрипт для глубокой диагностики проблем с отображением HTML-файлов

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
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

info() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# Проверяем, запущен ли скрипт с правами root
if [ "$EUID" -ne 0 ]; then
    error "Этот скрипт должен быть запущен с правами root"
    exit 1
fi

log "Начинаем глубокую диагностику проблем с отображением HTML-файлов..."

# Проверяем версию Nginx
log "Проверяем версию Nginx..."
nginx -v

# Проверяем статус Nginx
log "Проверяем статус Nginx..."
systemctl status nginx

# Проверяем конфигурацию Nginx
log "Проверяем конфигурацию Nginx..."
nginx -t

# Проверяем наличие директории public
log "Проверяем наличие директории public..."
if [ -d "/opt/SOKbot/public" ]; then
    log "Директория public существует."
    ls -la /opt/SOKbot/public
else
    error "Директория /opt/SOKbot/public не существует!"
    mkdir -p /opt/SOKbot/public
    chmod 755 /opt/SOKbot/public
    log "Директория public создана."
fi

# Проверяем наличие файла index.html
log "Проверяем наличие файла index.html..."
if [ -f "/opt/SOKbot/public/index.html" ]; then
    log "Файл index.html существует."
    ls -la /opt/SOKbot/public/index.html
    log "Первые 10 строк файла index.html:"
    head -n 10 /opt/SOKbot/public/index.html
else
    error "Файл /opt/SOKbot/public/index.html не существует!"
fi

# Проверяем наличие файла test.html
log "Проверяем наличие файла test.html..."
if [ -f "/opt/SOKbot/public/test.html" ]; then
    log "Файл test.html существует."
    ls -la /opt/SOKbot/public/test.html
    log "Первые 10 строк файла test.html:"
    head -n 10 /opt/SOKbot/public/test.html
else
    error "Файл /opt/SOKbot/public/test.html не существует!"
fi

# Проверяем наличие файла конфигурации Nginx
log "Проверяем наличие файла конфигурации Nginx..."
if [ -f "/etc/nginx/sites-available/telegram-bot.conf" ]; then
    log "Файл конфигурации Nginx существует."
    ls -la /etc/nginx/sites-available/telegram-bot.conf
    log "Содержимое файла конфигурации Nginx:"
    cat /etc/nginx/sites-available/telegram-bot.conf
else
    error "Файл /etc/nginx/sites-available/telegram-bot.conf не существует!"
fi

# Проверяем наличие символической ссылки
log "Проверяем наличие символической ссылки..."
if [ -L "/etc/nginx/sites-enabled/telegram-bot.conf" ]; then
    log "Символическая ссылка существует."
    ls -la /etc/nginx/sites-enabled/telegram-bot.conf
else
    error "Символическая ссылка /etc/nginx/sites-enabled/telegram-bot.conf не существует!"
    log "Создаем символическую ссылку..."
    ln -s /etc/nginx/sites-available/telegram-bot.conf /etc/nginx/sites-enabled/
fi

# Проверяем наличие файла mime.types
log "Проверяем наличие файла mime.types..."
if [ -f "/etc/nginx/mime.types" ]; then
    log "Файл mime.types существует."
    ls -la /etc/nginx/mime.types
    log "Проверяем наличие типа text/html в файле mime.types..."
    grep "text/html" /etc/nginx/mime.types
else
    error "Файл /etc/nginx/mime.types не существует!"
fi

# Проверяем права доступа
log "Проверяем права доступа..."
ls -la /opt/SOKbot
ls -la /opt/SOKbot/public

# Проверяем логи Nginx
log "Проверяем логи Nginx..."
log "Последние 20 строк error.log:"
tail -n 20 /var/log/nginx/error.log
log "Последние 20 строк access.log:"
tail -n 20 /var/log/nginx/access.log

# Проверяем доступность HTML-файлов локально
log "Проверяем доступность HTML-файлов локально..."
log "Запрос к index.html:"
curl -v http://localhost/index.html
log "Запрос к test.html:"
curl -v http://localhost/test.html

# Проверяем заголовки ответа
log "Проверяем заголовки ответа..."
log "Заголовки ответа для index.html:"
curl -I http://localhost/index.html
log "Заголовки ответа для test.html:"
curl -I http://localhost/test.html

# Проверяем SSL-сертификат
log "Проверяем SSL-сертификат..."
if [ -d "/etc/letsencrypt/live/srgolubev.ru" ]; then
    log "Директория сертификата существует."
    ls -la /etc/letsencrypt/live/srgolubev.ru
else
    error "Директория /etc/letsencrypt/live/srgolubev.ru не существует!"
fi

# Создаем тестовую страницу с минимальным HTML
log "Создаем тестовую страницу с минимальным HTML..."
cat > /opt/SOKbot/public/minimal.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Минимальная тестовая страница</title>
</head>
<body>
    <h1>Тестовая страница</h1>
    <p>Это минимальная тестовая страница.</p>
</body>
</html>
EOF
chown www-data:www-data /opt/SOKbot/public/minimal.html
chmod 644 /opt/SOKbot/public/minimal.html

# Создаем тестовую конфигурацию Nginx
log "Создаем тестовую конфигурацию Nginx..."
cat > /etc/nginx/sites-available/test.conf << 'EOF'
server {
    listen 80;
    server_name localhost;

    root /opt/SOKbot/public;
    index minimal.html;

    location / {
        try_files $uri $uri/ =404;
    }

    location ~ \.html$ {
        add_header Content-Type text/html;
    }
}
EOF

# Проверяем тестовую конфигурацию
log "Проверяем тестовую конфигурацию..."
nginx -t -c /etc/nginx/sites-available/test.conf

# Проверяем доступность по IP
log "Проверяем доступность по IP..."
log "Запрос к IP-адресу:"
curl -v http://95.163.234.54/minimal.html

# Проверяем наличие других конфигураций
log "Проверяем наличие других конфигураций..."
ls -la /etc/nginx/sites-enabled/

# Проверяем, не блокирует ли что-то доступ
log "Проверяем, не блокирует ли что-то доступ..."
log "Проверяем настройки брандмауэра:"
ufw status
log "Проверяем настройки SELinux:"
if command -v getenforce &> /dev/null; then
    getenforce
else
    log "SELinux не установлен."
fi

# Проверяем, не конфликтуют ли конфигурации
log "Проверяем, не конфликтуют ли конфигурации..."
grep -r "server_name srgolubev.ru" /etc/nginx/

# Проверяем, правильно ли настроен DNS
log "Проверяем, правильно ли настроен DNS..."
host srgolubev.ru

# Создаем новую конфигурацию Nginx с явным указанием типов
log "Создаем новую конфигурацию Nginx с явным указанием типов..."
cat > /etc/nginx/sites-available/telegram-bot.conf.new << 'EOF'
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

    # Включаем типы MIME
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Корневая директория для статических файлов
    root /opt/SOKbot/public;
    index index.html;

    # Основной маршрут для статических файлов
    location / {
        try_files $uri $uri/ =404;
    }
    
    # Явно указываем обработку HTML-файлов
    location ~ \.html$ {
        default_type text/html;
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

log "Проверяем новую конфигурацию..."
nginx -t -c /etc/nginx/sites-available/telegram-bot.conf.new

log "Рекомендации по исправлению:"
log "1. Переименуйте новую конфигурацию:"
log "   mv /etc/nginx/sites-available/telegram-bot.conf.new /etc/nginx/sites-available/telegram-bot.conf"
log "2. Перезапустите Nginx:"
log "   systemctl restart nginx"
log "3. Проверьте заголовки ответа:"
log "   curl -I https://srgolubev.ru"
log "4. Если проблема не решена, попробуйте создать тестовый виртуальный хост на порту 8080:"
log "   cp /etc/nginx/sites-available/test.conf /etc/nginx/sites-available/test8080.conf"
log "   sed -i 's/listen 80;/listen 8080;/' /etc/nginx/sites-available/test8080.conf"
log "   ln -s /etc/nginx/sites-available/test8080.conf /etc/nginx/sites-enabled/"
log "   systemctl restart nginx"
log "   curl -I http://localhost:8080/minimal.html"

log "Диагностика завершена."
