#!/bin/bash
# Скрипт для автоматического развертывания на сервере с ботом

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

# Функция для проверки наличия команды
check_command() {
    if ! command -v "$1" &> /dev/null; then
        warn "Команда $1 не найдена, устанавливаем..."
        return 1
    else
        return 0
    fi
}

# Функция для проверки порта
check_port() {
    if netstat -tuln | grep -q ":$1 "; then
        warn "Порт $1 уже используется:"
        netstat -tuln | grep ":$1 "
        return 1
    else
        return 0
    fi
}

# Проверяем, запущен ли скрипт с правами root
if [ "$EUID" -ne 0 ]; then
    error "Этот скрипт должен быть запущен с правами root"
    exit 1
fi

# Переходим в корневую директорию проекта
cd "$(dirname "$0")/.." || exit 1

log "Начинаем развертывание на сервере с ботом (212.224.118.58)..."
log "Текущая директория: $(pwd)"

# Проверяем наличие необходимых файлов
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    warn "Файл .env не найден, но найден .env.example. Копируем его..."
    cp .env.example .env
    warn "Пожалуйста, отредактируйте файл .env с правильными значениями."
elif [ ! -f ".env" ]; then
    error "Файл .env не найден. Пожалуйста, создайте его перед запуском скрипта."
    exit 1
fi

if [ ! -f "docker-compose.yml" ]; then
    error "Файл docker-compose.yml не найден. Пожалуйста, создайте его перед запуском скрипта."
    exit 1
fi

# Создаем директорию для логов, если она не существует
if [ ! -d "logs" ]; then
    log "Создаем директорию для логов..."
    mkdir -p logs
    chmod 755 logs
fi

# Создаем директорию для данных, если она не существует
if [ ! -d "data" ]; then
    log "Создаем директорию для данных..."
    mkdir -p data
    chmod 755 data
fi

# Устанавливаем необходимые пакеты
log "Проверяем и устанавливаем необходимые пакеты..."
apt-get update

# Проверяем и устанавливаем Docker
if ! check_command docker; then
    log "Устанавливаем Docker..."
    apt-get install -y docker.io
fi

# Проверяем и устанавливаем Docker Compose
if ! check_command docker-compose; then
    log "Устанавливаем Docker Compose..."
    apt-get install -y docker-compose
fi

# Проверяем и устанавливаем curl
if ! check_command curl; then
    log "Устанавливаем curl..."
    apt-get install -y curl
fi

# Проверяем и устанавливаем jq
if ! check_command jq; then
    log "Устанавливаем jq..."
    apt-get install -y jq
fi

# Проверяем и устанавливаем netstat
if ! check_command netstat; then
    log "Устанавливаем net-tools..."
    apt-get install -y net-tools
fi

# Проверяем и устанавливаем python3
if ! check_command python3; then
    log "Устанавливаем python3..."
    apt-get install -y python3 python3-pip
fi

# Проверяем и устанавливаем pip
if ! check_command pip3; then
    log "Устанавливаем pip3..."
    apt-get install -y python3-pip
fi

# Устанавливаем необходимые Python-пакеты
log "Устанавливаем необходимые Python-пакеты..."
pip3 install requests python-dotenv colorama

# Проверяем, запущен ли Docker
if ! systemctl is-active --quiet docker; then
    log "Запускаем Docker..."
    systemctl start docker
    systemctl enable docker
fi

# Проверяем, не занят ли порт 8000
if ! check_port 8000; then
    warn "Порт 8000 уже используется. Проверьте, не запущено ли уже приложение."
    read -p "Продолжить? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        error "Отмена развертывания."
        exit 1
    fi
fi

# Останавливаем существующие контейнеры
log "Останавливаем существующие контейнеры..."
docker-compose down

# Проверяем наличие образов и удаляем их при необходимости
if [[ $(docker images -q sokbot_app 2> /dev/null) ]]; then
    log "Удаляем существующие образы..."
    docker rmi sokbot_app
fi

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

# Настраиваем брандмауэр
log "Настраиваем брандмауэр..."
if check_command ufw; then
    # Разрешаем входящие соединения только с сервера с доменом
    ufw allow from 95.163.234.54 to any port 8000
    ufw status
else
    warn "ufw не установлен. Установите его вручную для настройки брандмауэра."
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

# Настраиваем ротацию логов
log "Настраиваем ротацию логов..."
cat > /etc/logrotate.d/telegram-bot << EOF
/opt/SOKbot/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 root root
}
EOF

# Создаем скрипт для проверки здоровья и перезапуска при необходимости
log "Создаем скрипт для проверки здоровья и перезапуска..."
cat > /opt/SOKbot/scripts/health_check_and_restart.sh << 'EOF'
#!/bin/bash

# Проверка здоровья и перезапуск при необходимости
HEALTH_URL="http://localhost:8000/health"
LOG_FILE="/opt/SOKbot/logs/health_check.log"

echo "$(date) - Проверка здоровья..." >> $LOG_FILE

if curl -s "$HEALTH_URL" | grep -q "ok"; then
    echo "$(date) - Сервис работает корректно." >> $LOG_FILE
else
    echo "$(date) - Сервис недоступен. Перезапускаем..." >> $LOG_FILE
    cd /opt/SOKbot
    docker-compose restart >> $LOG_FILE 2>&1
    sleep 10
    
    # Проверяем еще раз после перезапуска
    if curl -s "$HEALTH_URL" | grep -q "ok"; then
        echo "$(date) - Перезапуск успешен." >> $LOG_FILE
    else
        echo "$(date) - Перезапуск не помог. Требуется вмешательство." >> $LOG_FILE
        # Отправляем уведомление администратору (если настроено)
    fi
fi
EOF

chmod +x /opt/SOKbot/scripts/health_check_and_restart.sh

# Добавляем задачу в cron для периодической проверки здоровья
log "Добавляем задачу в cron для периодической проверки здоровья..."
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/SOKbot/scripts/health_check_and_restart.sh") | crontab -

# Проверяем работоспособность веб-сайта и вебхука
log "Проверяем работоспособность веб-сайта и вебхука..."
python3 scripts/check_website.py --skip-website --skip-test-page

log "Развертывание на сервере с ботом завершено успешно!"
log "Для проверки статуса запустите: docker-compose ps"
log "Для просмотра логов запустите: docker-compose logs -f"
log "Для проверки работоспособности запустите: curl http://localhost:8000/health"
