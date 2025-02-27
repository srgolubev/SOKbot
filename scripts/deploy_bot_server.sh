#!/bin/bash
# Скрипт для автоматического развертывания на сервере с ботом

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

log "Начинаем развертывание на сервере с ботом (212.224.118.58)..."

# Проверяем наличие необходимых файлов
if [ ! -f ".env" ]; then
    error "Файл .env не найден. Пожалуйста, создайте его перед запуском скрипта."
    exit 1
fi

if [ ! -f "docker-compose.yml" ]; then
    error "Файл docker-compose.yml не найден. Пожалуйста, создайте его перед запуском скрипта."
    exit 1
fi

# Устанавливаем необходимые пакеты
log "Устанавливаем необходимые пакеты..."
apt-get update
apt-get install -y docker.io docker-compose curl jq

# Проверяем, запущен ли Docker
if ! systemctl is-active --quiet docker; then
    log "Запускаем Docker..."
    systemctl start docker
    systemctl enable docker
fi

# Останавливаем существующие контейнеры
log "Останавливаем существующие контейнеры..."
docker-compose down

# Собираем и запускаем контейнеры
log "Собираем и запускаем контейнеры..."
docker-compose build
docker-compose up -d

# Проверяем, что контейнеры запущены
if [ "$(docker-compose ps -q | wc -l)" -gt 0 ]; then
    log "Контейнеры успешно запущены."
else
    error "Ошибка при запуске контейнеров."
    docker-compose logs
    exit 1
fi

# Настраиваем вебхук
log "Настраиваем вебхук Telegram..."
python3 scripts/setup_webhook.py

# Проверяем статус вебхука
log "Проверяем статус вебхука..."
python3 scripts/setup_webhook.py info

# Проверяем доступность API
log "Проверяем доступность API..."
source .env
HEALTH_URL="http://localhost:8000/health"
if curl -s "$HEALTH_URL" | grep -q "ok"; then
    log "API доступен и работает корректно."
else
    warn "API недоступен или возвращает ошибку."
    curl -v "$HEALTH_URL"
fi

# Настраиваем автозапуск при перезагрузке
log "Настраиваем автозапуск при перезагрузке..."
cat > /etc/systemd/system/telegram-bot.service << EOF
[Unit]
Description=Telegram Bot Service
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable telegram-bot.service

log "Развертывание на сервере с ботом завершено успешно!"
log "Для проверки статуса запустите: docker-compose ps"
log "Для просмотра логов запустите: docker-compose logs -f"
