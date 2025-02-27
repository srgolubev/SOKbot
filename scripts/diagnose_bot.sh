#!/bin/bash

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

log "Начинаем диагностику сервера бота..."

# Проверяем статус Docker
log "Проверяем статус Docker..."
if systemctl is-active --quiet docker; then
    log "Docker активен"
else
    error "Docker не запущен"
    systemctl start docker
fi

# Проверяем наличие контейнеров
log "Проверяем контейнеры..."
if [[ $(docker ps -q) ]]; then
    log "Запущенные контейнеры:"
    docker ps
else
    warn "Нет запущенных контейнеров"
fi

# Проверяем логи контейнера
log "Проверяем логи контейнера..."
if [[ $(docker ps -q -f name=sokbot) ]]; then
    log "Последние логи контейнера sokbot:"
    docker logs --tail 50 sokbot_app_1
else
    warn "Контейнер sokbot не найден"
fi

# Проверяем порт 8000
log "Проверяем порт 8000..."
if netstat -tuln | grep -q ":8000 "; then
    log "Порт 8000 прослушивается:"
    netstat -tuln | grep ":8000 "
else
    error "Порт 8000 не прослушивается"
fi

# Проверяем файл .env
log "Проверяем файл .env..."
if [ -f ".env" ]; then
    log "Файл .env существует"
    # Проверяем необходимые переменные
    source .env
    if [ -n "$TELEGRAM_TOKEN" ] && [ -n "$WEBHOOK_URL" ] && [ -n "$WEBHOOK_SECRET" ]; then
        log "Все необходимые переменные окружения найдены"
    else
        error "Отсутствуют некоторые переменные окружения"
    fi
else
    error "Файл .env не найден"
fi

# Проверяем firewall
log "Проверяем firewall..."
if command -v ufw &> /dev/null; then
    log "Статус UFW:"
    ufw status
else
    warn "UFW не установлен"
fi

# Проверяем доступность сервера бота локально
log "Проверяем доступность сервера бота локально..."
if curl -s "http://localhost:8000/health" > /dev/null; then
    log "Сервер бота доступен локально"
else
    error "Сервер бота не доступен локально"
fi

# Проверяем состояние контейнера
log "Проверяем состояние контейнера..."
docker inspect sokbot_app_1

# Пробуем перезапустить контейнер
log "Перезапускаем контейнер..."
docker-compose down
docker-compose up -d

# Ждем запуска
log "Ждем запуска контейнера..."
sleep 10

# Проверяем статус после перезапуска
log "Проверяем статус после перезапуска..."
if curl -s "http://localhost:8000/health" > /dev/null; then
    log "Сервер бота успешно запущен"
else
    error "Сервер бота не запустился после перезапуска"
    log "Последние логи после перезапуска:"
    docker logs --tail 50 sokbot_app_1
fi

log "Диагностика завершена."
