#!/bin/bash
# Скрипт для исправления конфигурации Nginx для корректного отображения HTML-файлов

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

log "Начинаем исправление конфигурации Nginx..."

# Создаем резервную копию текущей конфигурации
log "Создаем резервную копию текущей конфигурации..."
if [ -f "/etc/nginx/sites-available/telegram-bot.conf" ]; then
    cp /etc/nginx/sites-available/telegram-bot.conf /etc/nginx/sites-available/telegram-bot.conf.bak
    log "Резервная копия создана: /etc/nginx/sites-available/telegram-bot.conf.bak"
else
    warn "Файл конфигурации не найден. Будет создан новый файл."
fi

# Создаем новую конфигурацию Nginx
log "Создаем новую конфигурацию Nginx..."
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

    # Включаем типы MIME
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Основной маршрут для статических файлов
    location / {
        try_files $uri $uri/ =404;
    }

    # Обработка HTML-файлов
    location ~* \.html$ {
        types { text/html html htm; }
        default_type text/html;
        add_header Content-Type text/html;
    }

    # Обработка CSS-файлов
    location ~* \.css$ {
        types { text/css css; }
        default_type text/css;
        add_header Content-Type text/css;
    }

    # Обработка JS-файлов
    location ~* \.js$ {
        types { application/javascript js; }
        default_type application/javascript;
        add_header Content-Type application/javascript;
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
log "Проверяем конфигурацию Nginx..."
nginx -t
if [ $? -ne 0 ]; then
    error "Ошибка в конфигурации Nginx. Восстанавливаем из резервной копии..."
    if [ -f "/etc/nginx/sites-available/telegram-bot.conf.bak" ]; then
        cp /etc/nginx/sites-available/telegram-bot.conf.bak /etc/nginx/sites-available/telegram-bot.conf
        log "Конфигурация восстановлена из резервной копии."
    else
        error "Резервная копия не найдена. Конфигурация не восстановлена."
    fi
    exit 1
fi

# Проверяем наличие символической ссылки
log "Проверяем наличие символической ссылки..."
if [ ! -L "/etc/nginx/sites-enabled/telegram-bot.conf" ]; then
    log "Создаем символическую ссылку..."
    ln -s /etc/nginx/sites-available/telegram-bot.conf /etc/nginx/sites-enabled/
fi

# Создаем файл mime.types, если он не существует
log "Проверяем наличие файла mime.types..."
if [ ! -f "/etc/nginx/mime.types" ]; then
    log "Создаем файл mime.types..."
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

# Создаем минимальную тестовую страницу
log "Создаем минимальную тестовую страницу..."
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

# Устанавливаем правильные права доступа
log "Устанавливаем правильные права доступа..."
chown -R www-data:www-data /opt/SOKbot/public
chmod -R 755 /opt/SOKbot/public
chmod 644 /opt/SOKbot/public/*.html

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
log "Заголовки ответа для index.html:"
curl -I http://localhost/index.html
log "Заголовки ответа для minimal.html:"
curl -I http://localhost/minimal.html

log "Исправление конфигурации Nginx завершено."
log "Проверьте доступность сайта по адресу: https://srgolubev.ru"
log "Проверьте тестовую страницу по адресу: https://srgolubev.ru/minimal.html"

log "Если проблема не решена, выполните следующие шаги:"
log "1. Проверьте логи Nginx:"
log "   tail -f /var/log/nginx/error.log"
log "   tail -f /var/log/nginx/access.log"
log "2. Проверьте заголовки ответа:"
log "   curl -I https://srgolubev.ru"
log "3. Проверьте конфигурацию Nginx:"
log "   nginx -t"
log "4. Перезапустите Nginx:"
log "   systemctl restart nginx"
