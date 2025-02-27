#!/bin/bash
# Скрипт для обновления сервера с ботом

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
cd /opt/SOKbot || exit 1

log "Начинаем обновление сервера с ботом (212.224.118.58)..."
log "Текущая директория: $(pwd)"

# Сохраняем текущую версию для возможного отката
CURRENT_COMMIT=$(git rev-parse HEAD)
log "Текущая версия: $CURRENT_COMMIT"

# Создаем резервную копию .env файла
if [ -f ".env" ]; then
    log "Создаем резервную копию .env файла..."
    cp .env .env.backup
fi

# Обновляем код из репозитория
log "Обновляем код из репозитория..."
git fetch origin
git reset --hard origin/master

# Проверяем, что обновление прошло успешно
if [ $? -ne 0 ]; then
    error "Ошибка при обновлении кода. Откатываем изменения..."
    git reset --hard $CURRENT_COMMIT
    if [ -f ".env.backup" ]; then
        mv .env.backup .env
    fi
    exit 1
fi

# Восстанавливаем .env файл
if [ -f ".env.backup" ]; then
    log "Восстанавливаем .env файл..."
    mv .env.backup .env
fi

# Обновляем зависимости Python (если необходимо)
if [ -f "requirements.txt" ]; then
    log "Обновляем зависимости Python..."
    pip3 install -r requirements.txt
fi

# Останавливаем существующие контейнеры
log "Останавливаем существующие контейнеры..."
docker-compose down

# Удаляем старые образы
log "Удаляем старые образы..."
docker images | grep "sokbot_app" | awk '{print $3}' | xargs -r docker rmi

# Собираем и запускаем контейнеры
log "Собираем и запускаем контейнеры..."
docker-compose build --no-cache
docker-compose up -d

# Проверяем, что контейнеры запущены
if [ "$(docker-compose ps -q | wc -l)" -gt 0 ]; then
    log "Контейнеры успешно запущены."
else
    error "Ошибка при запуске контейнеров."
    docker-compose logs
    exit 1
fi

# Ждем, пока приложение запустится
log "Ждем, пока приложение запустится..."
sleep 10

# Проверяем доступность API
log "Проверяем доступность API..."
HEALTH_URL="http://localhost:8000/health"
if curl -s "$HEALTH_URL" | grep -q "ok"; then
    log "API доступен и работает корректно."
else
    warn "API недоступен или возвращает ошибку."
    curl -v "$HEALTH_URL"
    
    # Спрашиваем, нужно ли откатить изменения
    read -p "API недоступен. Откатить изменения? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "Откатываем изменения..."
        docker-compose down
        git reset --hard $CURRENT_COMMIT
        docker-compose up -d
        log "Изменения откачены. Проверьте работоспособность системы."
        exit 1
    fi
fi

# Обновляем вебхук
log "Обновляем вебхук Telegram..."
python3 scripts/setup_webhook.py

# Проверяем статус вебхука
log "Проверяем статус вебхука..."
python3 scripts/setup_webhook.py info

# Проверяем работоспособность веб-сайта и вебхука
log "Проверяем работоспособность веб-сайта и вебхука..."
python3 scripts/check_website.py --skip-website --skip-test-page

# Очищаем неиспользуемые образы и контейнеры
log "Очищаем неиспользуемые образы и контейнеры..."
docker system prune -f

log "Обновление сервера с ботом завершено успешно!"
log "Для проверки статуса запустите: docker-compose ps"
log "Для просмотра логов запустите: docker-compose logs -f"
log "Для проверки работоспособности запустите: curl http://localhost:8000/health"
