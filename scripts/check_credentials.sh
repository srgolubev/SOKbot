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

log "Начинаем проверку учетных данных..."

# Проверяем наличие директории credentials
log "Проверяем директорию credentials..."
if [ ! -d "credentials" ]; then
    warn "Директория credentials не существует"
    log "Создаем директорию credentials..."
    mkdir -p credentials
    chmod 755 credentials
fi

# Проверяем наличие файла client_secrets.json
log "Проверяем файл client_secrets.json..."
if [ -f "credentials/client_secrets.json" ]; then
    log "Файл client_secrets.json существует"
    
    # Проверяем права доступа
    PERMS=$(stat -c "%a" credentials/client_secrets.json)
    if [ "$PERMS" != "644" ]; then
        warn "Неправильные права доступа: $PERMS"
        log "Устанавливаем правильные права доступа..."
        chmod 644 credentials/client_secrets.json
    fi
    
    # Проверяем владельца
    OWNER=$(stat -c "%U:%G" credentials/client_secrets.json)
    if [ "$OWNER" != "www-data:www-data" ]; then
        warn "Неправильный владелец: $OWNER"
        log "Устанавливаем правильного владельца..."
        chown www-data:www-data credentials/client_secrets.json
    fi
    
    # Проверяем валидность JSON
    if jq empty credentials/client_secrets.json 2>/dev/null; then
        log "Файл содержит валидный JSON"
        
        # Проверяем наличие необходимых полей
        if jq -e '.installed' credentials/client_secrets.json >/dev/null; then
            log "Файл содержит необходимые поля конфигурации"
        else
            error "Файл не содержит необходимой конфигурации Google API"
        fi
    else
        error "Файл содержит невалидный JSON"
    fi
else
    error "Файл credentials/client_secrets.json не найден"
    error "Необходимо создать проект в Google Cloud Console и скачать учетные данные"
    log "Инструкция:"
    log "1. Перейдите в Google Cloud Console: https://console.cloud.google.com/"
    log "2. Создайте новый проект или выберите существующий"
    log "3. Включите Google Sheets API"
    log "4. Создайте учетные данные (OAuth 2.0 Client ID)"
    log "5. Скачайте JSON файл"
    log "6. Переименуйте его в client_secrets.json"
    log "7. Поместите файл в директорию credentials"
fi

# Проверяем наличие файла token.json
log "Проверяем файл token.json..."
if [ -f "credentials/token.json" ]; then
    log "Файл token.json существует"
    
    # Проверяем права доступа
    PERMS=$(stat -c "%a" credentials/token.json)
    if [ "$PERMS" != "644" ]; then
        warn "Неправильные права доступа: $PERMS"
        log "Устанавливаем правильные права доступа..."
        chmod 644 credentials/token.json
    fi
    
    # Проверяем владельца
    OWNER=$(stat -c "%U:%G" credentials/token.json)
    if [ "$OWNER" != "www-data:www-data" ]; then
        warn "Неправильный владелец: $OWNER"
        log "Устанавливаем правильного владельца..."
        chown www-data:www-data credentials/token.json
    fi
else
    warn "Файл token.json не найден"
    log "Файл будет создан автоматически при первой авторизации"
fi

# Проверяем права на директорию
log "Проверяем права на директорию credentials..."
PERMS=$(stat -c "%a" credentials)
if [ "$PERMS" != "755" ]; then
    warn "Неправильные права доступа на директорию: $PERMS"
    log "Устанавливаем правильные права доступа..."
    chmod 755 credentials
fi

OWNER=$(stat -c "%U:%G" credentials)
if [ "$OWNER" != "www-data:www-data" ]; then
    warn "Неправильный владелец директории: $OWNER"
    log "Устанавливаем правильного владельца..."
    chown www-data:www-data credentials
fi

log "Проверка учетных данных завершена."
