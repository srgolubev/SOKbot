#!/bin/bash
# Скрипт для исправления проблем с MIME-типами и отображением HTML-файлов

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

log "Начинаем исправление проблем с MIME-типами и отображением HTML-файлов..."

# Проверяем наличие директории public
if [ ! -d "/opt/SOKbot/public" ]; then
    log "Директория public не существует. Создаем..."
    mkdir -p /opt/SOKbot/public
    chmod 755 /opt/SOKbot/public
fi

# Создаем тестовую страницу
log "Создаем тестовую страницу..."
cat > /opt/SOKbot/public/test.html << 'EOF'
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

# Копируем существующий index.html, если он есть
if [ -f "/opt/SOKbot/public/index.html" ]; then
    log "Копируем существующий index.html..."
    cp /opt/SOKbot/public/index.html /opt/SOKbot/public/index.html.bak
fi

# Создаем новый index.html
log "Создаем новый index.html..."
cat > /opt/SOKbot/public/index.html << 'EOF'
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>srgolubev.ru</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Roboto:wght@300;400&display=swap" rel="stylesheet">
    <style>
        :root {
            /* Цвет Pantone 2025 года - Peach Fuzz (PANTONE 13-1023) */
            --pantone-2025: #FFBE98;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Roboto', sans-serif;
            background-color: var(--pantone-2025);
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            color: #333;
            text-align: center;
            overflow: hidden;
            position: relative;
        }
        
        .container {
            padding: 2rem;
            background-color: rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            z-index: 10;
            animation: fadeIn 1.5s ease-out;
        }
        
        h1 {
            font-family: 'Playfair Display', serif;
            font-size: 5rem;
            margin-bottom: 1.5rem;
            background: linear-gradient(45deg, #333, #000);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
            letter-spacing: 2px;
        }
        
        .countdown {
            font-size: 1.8rem;
            margin-top: 2rem;
            display: flex;
            justify-content: center;
            gap: 1.5rem;
        }
        
        .countdown-item {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        
        .countdown-value {
            font-size: 2.5rem;
            font-weight: bold;
            background: rgba(255, 255, 255, 0.3);
            padding: 0.5rem 1rem;
            border-radius: 10px;
            min-width: 80px;
        }
        
        .countdown-label {
            font-size: 0.9rem;
            margin-top: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            opacity: 0.8;
        }
        
        .circles {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
            z-index: 1;
        }
        
        .circles li {
            position: absolute;
            display: block;
            list-style: none;
            width: 20px;
            height: 20px;
            background: rgba(255, 255, 255, 0.2);
            animation: animate 25s linear infinite;
            bottom: -150px;
            border-radius: 50%;
        }
        
        .circles li:nth-child(1) {
            left: 25%;
            width: 80px;
            height: 80px;
            animation-delay: 0s;
        }
        
        .circles li:nth-child(2) {
            left: 10%;
            width: 20px;
            height: 20px;
            animation-delay: 2s;
            animation-duration: 12s;
        }
        
        .circles li:nth-child(3) {
            left: 70%;
            width: 20px;
            height: 20px;
            animation-delay: 4s;
        }
        
        .circles li:nth-child(4) {
            left: 40%;
            width: 60px;
            height: 60px;
            animation-delay: 0s;
            animation-duration: 18s;
        }
        
        .circles li:nth-child(5) {
            left: 65%;
            width: 20px;
            height: 20px;
            animation-delay: 0s;
        }
        
        .circles li:nth-child(6) {
            left: 75%;
            width: 110px;
            height: 110px;
            animation-delay: 3s;
        }
        
        .circles li:nth-child(7) {
            left: 35%;
            width: 150px;
            height: 150px;
            animation-delay: 7s;
        }
        
        .circles li:nth-child(8) {
            left: 50%;
            width: 25px;
            height: 25px;
            animation-delay: 15s;
            animation-duration: 45s;
        }
        
        .circles li:nth-child(9) {
            left: 20%;
            width: 15px;
            height: 15px;
            animation-delay: 2s;
            animation-duration: 35s;
        }
        
        .circles li:nth-child(10) {
            left: 85%;
            width: 150px;
            height: 150px;
            animation-delay: 0s;
            animation-duration: 11s;
        }
        
        @keyframes animate {
            0% {
                transform: translateY(0) rotate(0deg);
                opacity: 1;
                border-radius: 0;
            }
            100% {
                transform: translateY(-1000px) rotate(720deg);
                opacity: 0;
                border-radius: 50%;
            }
        }
        
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @media (max-width: 768px) {
            h1 {
                font-size: 3rem;
            }
            
            .countdown {
                font-size: 1.2rem;
                flex-wrap: wrap;
            }
            
            .countdown-value {
                font-size: 1.8rem;
                min-width: 60px;
            }
        }
    </style>
</head>
<body>
    <ul class="circles">
        <li></li>
        <li></li>
        <li></li>
        <li></li>
        <li></li>
        <li></li>
        <li></li>
        <li></li>
        <li></li>
        <li></li>
    </ul>
    
    <div class="container">
        <h1>srgolubev</h1>
        <div class="countdown">
            <div class="countdown-item">
                <div id="days" class="countdown-value">00</div>
                <div class="countdown-label">дней</div>
            </div>
            <div class="countdown-item">
                <div id="hours" class="countdown-value">00</div>
                <div class="countdown-label">часов</div>
            </div>
            <div class="countdown-item">
                <div id="minutes" class="countdown-value">00</div>
                <div class="countdown-label">минут</div>
            </div>
            <div class="countdown-item">
                <div id="seconds" class="countdown-value">00</div>
                <div class="countdown-label">секунд</div>
            </div>
        </div>
    </div>
    
    <script>
        // Устанавливаем дату окончания (1:30 16 января 2026 по московскому времени)
        const endDate = new Date('January 16, 2026 01:30:00 GMT+0300').getTime();
        
        // Обновляем таймер каждую секунду
        const countdown = setInterval(function() {
            // Получаем текущую дату и время
            const now = new Date().getTime();
            
            // Находим разницу между текущим временем и датой окончания
            const distance = endDate - now;
            
            // Рассчитываем дни, часы, минуты и секунды
            const days = Math.floor(distance / (1000 * 60 * 60 * 24));
            const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((distance % (1000 * 60)) / 1000);
            
            // Отображаем результат
            document.getElementById('days').innerHTML = days.toString().padStart(2, '0');
            document.getElementById('hours').innerHTML = hours.toString().padStart(2, '0');
            document.getElementById('minutes').innerHTML = minutes.toString().padStart(2, '0');
            document.getElementById('seconds').innerHTML = seconds.toString().padStart(2, '0');
            
            // Если таймер истек, отображаем сообщение
            if (distance < 0) {
                clearInterval(countdown);
                document.getElementById('days').innerHTML = "00";
                document.getElementById('hours').innerHTML = "00";
                document.getElementById('minutes').innerHTML = "00";
                document.getElementById('seconds').innerHTML = "00";
            }
        }, 1000);
    </script>
</body>
</html>
EOF

# Устанавливаем правильные права доступа
log "Устанавливаем правильные права доступа..."
chown -R www-data:www-data /opt/SOKbot/public
chmod -R 755 /opt/SOKbot/public
chmod 644 /opt/SOKbot/public/*.html

# Обновляем конфигурацию Nginx
log "Обновляем конфигурацию Nginx..."

# Создаем новую конфигурацию
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
    
    # Явно указываем MIME-типы для HTML и CSS
    types {
        text/html html htm;
        text/css css;
        application/javascript js;
    }

    # Корневая директория для статических файлов
    root /opt/SOKbot/public;
    index index.html;

    # Основной маршрут для статических файлов
    location / {
        try_files $uri $uri/ /index.html;
        add_header Content-Type text/html;
    }
    
    # Явно указываем обработку HTML-файлов
    location ~ \.html$ {
        add_header Content-Type text/html;
    }
    
    # Явно указываем обработку CSS-файлов
    location ~ \.css$ {
        add_header Content-Type text/css;
    }
    
    # Явно указываем обработку JS-файлов
    location ~ \.js$ {
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

log "Исправление проблем с MIME-типами и отображением HTML-файлов завершено."
log "Проверьте доступность сайта по адресу: https://srgolubev.ru"
log "Проверьте тестовую страницу по адресу: https://srgolubev.ru/test.html"
