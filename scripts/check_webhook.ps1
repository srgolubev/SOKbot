# Скрипт PowerShell для проверки статуса вебхука Telegram бота

# Функция для загрузки переменных окружения из .env файла
function Load-EnvFile {
    param (
        [string]$envFile
    )
    
    if (Test-Path $envFile) {
        Get-Content $envFile | ForEach-Object {
            if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
                $key = $matches[1].Trim()
                $value = $matches[2].Trim()
                [Environment]::SetEnvironmentVariable($key, $value, "Process")
            }
        }
    } else {
        Write-Error "Файл .env не найден. Пожалуйста, создайте его с переменной TELEGRAM_TOKEN."
        exit 1
    }
}

# Загружаем переменные окружения
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$envFile = Join-Path (Split-Path -Parent $scriptDir) ".env"
Load-EnvFile -envFile $envFile

# Проверяем, что TELEGRAM_TOKEN установлен
if (-not $env:TELEGRAM_TOKEN) {
    Write-Error "TELEGRAM_TOKEN не найден в переменных окружения."
    exit 1
}

# Получаем информацию о вебхуке
Write-Host "Получаем информацию о вебхуке для бота..." -ForegroundColor Cyan
$webhookInfo = Invoke-RestMethod -Uri "https://api.telegram.org/bot$env:TELEGRAM_TOKEN/getWebhookInfo" -Method Get
$webhookInfo | ConvertTo-Json -Depth 3

# Проверяем доступность вебхука
if ($env:WEBHOOK_URL) {
    Write-Host "`nПроверяем доступность вебхука по URL: $env:WEBHOOK_URL" -ForegroundColor Cyan
    try {
        $response = Invoke-WebRequest -Uri $env:WEBHOOK_URL -Method Head -ErrorAction SilentlyContinue
        Write-Host $response.StatusCode $response.StatusDescription -ForegroundColor Green
    } catch {
        Write-Host "Ошибка при подключении к $env:WEBHOOK_URL" -ForegroundColor Red
        Write-Host $_.Exception.Message
    }
    
    # Проверяем /webhook/telegram эндпоинт
    Write-Host "`nПроверяем доступность /webhook/telegram эндпоинта:" -ForegroundColor Cyan
    try {
        $telegramEndpoint = "$env:WEBHOOK_URL/telegram"
        $response = Invoke-WebRequest -Uri $telegramEndpoint -Method Head -ErrorAction SilentlyContinue
        Write-Host $response.StatusCode $response.StatusDescription -ForegroundColor Green
    } catch {
        Write-Host "Ошибка при подключении к $telegramEndpoint" -ForegroundColor Red
        Write-Host $_.Exception.Message
    }
} else {
    Write-Host "WEBHOOK_URL не найден в переменных окружения." -ForegroundColor Yellow
}

# Проверяем статус сервера с ботом
Write-Host "`nПроверяем доступность сервера с ботом (212.224.118.58):" -ForegroundColor Cyan
$botServerPing = Test-Connection -ComputerName 212.224.118.58 -Count 3 -ErrorAction SilentlyContinue
if ($botServerPing) {
    $botServerPing | ForEach-Object { Write-Host "Ответ от 212.224.118.58: время=$($_.ResponseTime)мс" -ForegroundColor Green }
} else {
    Write-Host "Сервер с ботом (212.224.118.58) недоступен" -ForegroundColor Red
}

# Проверяем статус сервера с доменом
Write-Host "`nПроверяем доступность сервера с доменом (95.163.234.54):" -ForegroundColor Cyan
$domainServerPing = Test-Connection -ComputerName 95.163.234.54 -Count 3 -ErrorAction SilentlyContinue
if ($domainServerPing) {
    $domainServerPing | ForEach-Object { Write-Host "Ответ от 95.163.234.54: время=$($_.ResponseTime)мс" -ForegroundColor Green }
} else {
    Write-Host "Сервер с доменом (95.163.234.54) недоступен" -ForegroundColor Red
}

Write-Host "`nПроверка завершена." -ForegroundColor Cyan
