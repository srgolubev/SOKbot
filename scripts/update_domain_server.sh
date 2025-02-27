#!/bin/bash
# Скрипт для обновления сервера с доменом

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

log "Начинаем обновление сервера с доменом (95.163.234.54)..."

# Обновляем репозиторий
log "Обновляем репозиторий..."
git pull

# Создаем директорию для публичных файлов, если она не существует
log "Создаем директорию для публичных файлов..."
mkdir -p /opt/SOKbot/public

# Обновляем конфигурацию Nginx
log "Обновляем конфигурацию Nginx..."
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

# Проверяем доступность домена
log "Проверяем доступность домена..."
if curl -s -I https://srgolubev.ru | grep -q "200 OK"; then
    log "Домен доступен и работает корректно."
else
    warn "Домен недоступен или возвращает ошибку."
    curl -v https://srgolubev.ru
fi

log "Обновление сервера с доменом завершено успешно!"
