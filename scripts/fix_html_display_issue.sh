#!/bin/bash
# Скрипт для диагностики и исправления проблем с отображением HTML-файлов

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

# Переходим в директорию проекта
cd /opt/SOKbot || {
    error "Директория /opt/SOKbot не существует"
    exit 1
}

log "Начинаем диагностику и исправление проблем с отображением HTML-файлов..."

# Проверяем наличие директории public
if [ ! -d "public" ]; then
    log "Директория public не существует. Создаем..."
    mkdir -p public
    chmod 755 public
fi

# Проверяем наличие файла index.html
if [ ! -f "public/index.html" ]; then
    warn "Файл public/index.html не существует."
    
    # Проверяем, есть ли файл в репозитории
    if [ -f "public/index.html" ]; then
        log "Файл index.html найден в репозитории. Копируем..."
        cp public/index.html public/index.html
    else
        log "Создаем тестовый файл index.html..."
        cat > public/index.html << 'EOF'
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Тестовая страница</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #FFBE98;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .container {
            background-color: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
        h1 {
            color: #333;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Тестовая страница</h1>
        <p>Если вы видите эту страницу, значит HTML-файлы отображаются корректно.</p>
        <p>Текущее время: <span id="current-time"></span></p>
    </div>
    
    <script>
        // Обновляем время каждую секунду
        function updateTime() {
            const now = new Date();
            document.getElementById('current-time').textContent = now.toLocaleTimeString();
        }
        
        updateTime();
        setInterval(updateTime, 1000);
    </script>
</body>
</html>
EOF
    fi
fi

# Проверяем права доступа
log "Проверяем и исправляем права доступа..."
chown -R www-data:www-data public
chmod -R 755 public

# Проверяем конфигурацию Nginx
log "Проверяем конфигурацию Nginx..."

# Проверяем наличие файла конфигурации
if [ ! -f "/etc/nginx/sites-available/telegram-bot.conf" ]; then
    warn "Файл конфигурации Nginx не найден. Создаем..."
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

    # Включаем типы MIME
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Корневая директория для статических файлов
    root /opt/SOKbot/public;
    index index.html;

    # Основной маршрут для статических файлов
    location / {
        try_files $uri $uri/ /index.html;
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

    # Создаем символическую ссылку
    if [ ! -L "/etc/nginx/sites-enabled/telegram-bot.conf" ]; then
        ln -s /etc/nginx/sites-available/telegram-bot.conf /etc/nginx/sites-enabled/
    fi
else
    # Обновляем существующую конфигурацию
    log "Обновляем существующую конфигурацию Nginx..."
    
    # Проверяем наличие директивы include mime.types
    if ! grep -q "include /etc/nginx/mime.types" /etc/nginx/sites-available/telegram-bot.conf; then
        sed -i '/listen 443 ssl;/a \    # Включаем типы MIME\n    include /etc/nginx/mime.types;\n    default_type application/octet-stream;' /etc/nginx/sites-available/telegram-bot.conf
    fi
    
    # Проверяем и обновляем location /
    if grep -q "try_files \$uri \$uri/ =404" /etc/nginx/sites-available/telegram-bot.conf; then
        sed -i 's/try_files \$uri \$uri\/ =404;/try_files \$uri \$uri\/ \/index.html;/' /etc/nginx/sites-available/telegram-bot.conf
    fi
fi

# Проверяем наличие файла mime.types
if [ ! -f "/etc/nginx/mime.types" ]; then
    warn "Файл mime.types не найден. Создаем..."
    cat > /etc/nginx/mime.types << 'EOF'
types {
    text/html                             html htm shtml;
    text/css                              css;
    text/xml                              xml;
    image/gif                             gif;
    image/jpeg                            jpeg jpg;
    application/javascript                js;
    application/atom+xml                  atom;
    application/rss+xml                   rss;

    text/mathml                           mml;
    text/plain                            txt;
    text/vnd.sun.j2me.app-descriptor      jad;
    text/vnd.wap.wml                      wml;
    text/x-component                      htc;

    image/png                             png;
    image/tiff                            tif tiff;
    image/vnd.wap.wbmp                    wbmp;
    image/x-icon                          ico;
    image/x-jng                           jng;
    image/x-ms-bmp                        bmp;
    image/svg+xml                         svg svgz;
    image/webp                            webp;

    application/font-woff                 woff;
    application/java-archive              jar war ear;
    application/json                      json;
    application/mac-binhex40              hqx;
    application/msword                    doc;
    application/pdf                       pdf;
    application/postscript                ps eps ai;
    application/rtf                       rtf;
    application/vnd.apple.mpegurl         m3u8;
    application/vnd.ms-excel              xls;
    application/vnd.ms-fontobject         eot;
    application/vnd.ms-powerpoint         ppt;
    application/vnd.wap.wmlc              wmlc;
    application/vnd.google-earth.kml+xml  kml;
    application/vnd.google-earth.kmz      kmz;
    application/x-7z-compressed           7z;
    application/x-cocoa                   cco;
    application/x-java-archive-diff       jardiff;
    application/x-java-jnlp-file          jnlp;
    application/x-makeself                run;
    application/x-perl                    pl pm;
    application/x-pilot                   prc pdb;
    application/x-rar-compressed          rar;
    application/x-redhat-package-manager  rpm;
    application/x-sea                     sea;
    application/x-shockwave-flash         swf;
    application/x-stuffit                 sit;
    application/x-tcl                     tcl tk;
    application/x-x509-ca-cert            der pem crt;
    application/x-xpinstall               xpi;
    application/xhtml+xml                 xhtml;
    application/xspf+xml                  xspf;
    application/zip                       zip;

    application/octet-stream              bin exe dll;
    application/octet-stream              deb;
    application/octet-stream              dmg;
    application/octet-stream              iso img;
    application/octet-stream              msi msp msm;

    application/vnd.openxmlformats-officedocument.wordprocessingml.document    docx;
    application/vnd.openxmlformats-officedocument.spreadsheetml.sheet          xlsx;
    application/vnd.openxmlformats-officedocument.presentationml.presentation  pptx;

    audio/midi                            mid midi kar;
    audio/mpeg                            mp3;
    audio/ogg                             ogg;
    audio/x-m4a                           m4a;
    audio/x-realaudio                     ra;

    video/3gpp                            3gpp 3gp;
    video/mp2t                            ts;
    video/mp4                             mp4;
    video/mpeg                            mpeg mpg;
    video/quicktime                       mov;
    video/webm                            webm;
    video/x-flv                           flv;
    video/x-m4v                           m4v;
    video/x-mng                           mng;
    video/x-ms-asf                        asx asf;
    video/x-ms-wmv                        wmv;
    video/x-msvideo                       avi;
}
EOF
fi

# Проверяем конфигурацию Nginx
log "Проверяем конфигурацию Nginx..."
nginx -t
if [ $? -ne 0 ]; then
    error "Ошибка в конфигурации Nginx."
    exit 1
fi

# Перезапускаем Nginx
log "Перезапускаем Nginx..."
systemctl restart nginx

# Проверяем, запущен ли Nginx
if ! systemctl is-active --quiet nginx; then
    error "Nginx не запущен после перезапуска."
    systemctl status nginx
    exit 1
fi

# Проверяем доступность HTML-файлов
log "Проверяем доступность HTML-файлов..."
curl -s -o /dev/null -w "%{http_code}" http://localhost/index.html
HTTP_CODE=$?

if [ $HTTP_CODE -eq 200 ]; then
    log "HTML-файлы доступны локально."
else
    warn "HTML-файлы недоступны локально. HTTP-код: $HTTP_CODE"
fi

# Проверяем доступность через домен
log "Проверяем доступность через домен..."
curl -s -o /dev/null -w "%{http_code}" https://srgolubev.ru/index.html
HTTP_CODE=$?

if [ $HTTP_CODE -eq 200 ]; then
    log "HTML-файлы доступны через домен."
else
    warn "HTML-файлы недоступны через домен. HTTP-код: $HTTP_CODE"
    
    # Проверяем SSL-сертификат
    log "Проверяем SSL-сертификат..."
    if [ ! -d "/etc/letsencrypt/live/srgolubev.ru" ]; then
        warn "SSL-сертификат не найден. Запускаем certbot..."
        certbot --nginx -d srgolubev.ru
    fi
fi

# Создаем тестовую страницу
log "Создаем тестовую страницу..."
cat > public/test.html << 'EOF'
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Тестовая страница</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #FFBE98;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .container {
            background-color: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
        h1 {
            color: #333;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Тестовая страница</h1>
        <p>Если вы видите эту страницу, значит HTML-файлы отображаются корректно.</p>
        <p>Текущее время: <span id="current-time"></span></p>
    </div>
    
    <script>
        // Обновляем время каждую секунду
        function updateTime() {
            const now = new Date();
            document.getElementById('current-time').textContent = now.toLocaleTimeString();
        }
        
        updateTime();
        setInterval(updateTime, 1000);
    </script>
</body>
</html>
EOF

# Устанавливаем правильные права доступа
chown www-data:www-data public/test.html
chmod 644 public/test.html

log "Диагностика и исправление проблем с отображением HTML-файлов завершены."
log "Проверьте доступность сайта по адресу: https://srgolubev.ru"
log "Проверьте тестовую страницу по адресу: https://srgolubev.ru/test.html"
