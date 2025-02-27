#!/bin/bash
# Скрипт для автоматического развертывания на сервере с доменом

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

# Переходим в корневую директорию проекта
cd "$(dirname "$0")/.." || exit 1

log "Начинаем развертывание на сервере с доменом (95.163.234.54)..."

# Проверяем наличие необходимых файлов
if [ ! -f "nginx/telegram-bot.conf" ]; then
    error "Файл nginx/telegram-bot.conf не найден. Пожалуйста, создайте его перед запуском скрипта."
    exit 1
fi

# Устанавливаем необходимые пакеты
log "Устанавливаем необходимые пакеты..."
apt-get update
apt-get install -y nginx certbot python3-certbot-nginx curl

# Настраиваем Nginx
log "Настраиваем Nginx..."
cp nginx/telegram-bot.conf /etc/nginx/sites-available/
ln -sf /etc/nginx/sites-available/telegram-bot.conf /etc/nginx/sites-enabled/

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
systemctl enable nginx

# Настраиваем SSL-сертификат
log "Настраиваем SSL-сертификат..."
certbot --nginx -d srgolubev.ru --non-interactive --agree-tos --email admin@srgolubev.ru

# Проверяем доступность домена
log "Проверяем доступность домена..."
if curl -s -I https://srgolubev.ru | grep -q "200 OK"; then
    log "Домен доступен и работает корректно."
else
    warn "Домен недоступен или возвращает ошибку."
    curl -v https://srgolubev.ru
fi

# Проверяем доступность вебхука
log "Проверяем доступность вебхука..."
if curl -s -I https://srgolubev.ru/webhook | grep -q "404 Not Found"; then
    log "Эндпоинт вебхука доступен (ожидаемый ответ 404)."
else
    warn "Эндпоинт вебхука недоступен или возвращает неожиданный ответ."
    curl -v https://srgolubev.ru/webhook
fi

# Настраиваем автообновление SSL-сертификата
log "Настраиваем автообновление SSL-сертификата..."
echo "0 0,12 * * * root python -c 'import random; import time; time.sleep(random.random() * 3600)' && certbot renew -q" > /etc/cron.d/certbot-renew

# Настраиваем файрвол
log "Настраиваем файрвол..."
apt-get install -y ufw
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Разрешаем доступ только с сервера с ботом
log "Настраиваем правила доступа для сервера с ботом..."
ufw allow from 212.224.118.58 to any port 80
ufw allow from 212.224.118.58 to any port 443

log "Развертывание на сервере с доменом завершено успешно!"
log "Для проверки статуса Nginx запустите: systemctl status nginx"
log "Для проверки SSL-сертификата запустите: certbot certificates"
