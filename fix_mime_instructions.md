# Инструкция по исправлению проблем с MIME-типами

Для исправления проблем с отображением HTML-файлов и MIME-типами на сервере с доменом (95.163.234.54), выполните следующие шаги:

## 1. Подключитесь к серверу по SSH

```bash
ssh username@95.163.234.54
```

## 2. Обновите репозиторий

Перейдите в директорию проекта и обновите репозиторий:

```bash
cd /opt/SOKbot
git pull
```

## 3. Сделайте скрипт исполняемым

```bash
chmod +x scripts/fix_mime_issues.sh
```

## 4. Запустите скрипт с правами root

```bash
sudo ./scripts/fix_mime_issues.sh
```

Этот скрипт специально создан для исправления проблем с MIME-типами и отображением HTML-файлов. Он выполнит следующие действия:

1. Создаст новую конфигурацию Nginx с явным указанием MIME-типов
2. Добавит заголовки Content-Type для HTML, CSS и JS файлов
3. Создаст новые версии index.html и test.html
4. Установит правильные права доступа
5. Перезапустит Nginx

## 5. Проверьте результат

После выполнения скрипта проверьте, что страницы отображаются корректно:

1. Откройте в браузере: https://srgolubev.ru
2. Также проверьте тестовую страницу: https://srgolubev.ru/test.html

## Ручное исправление (если скрипт не помог)

Если скрипт не решил проблему, выполните следующие шаги вручную:

### 1. Проверьте конфигурацию Nginx

```bash
sudo nano /etc/nginx/sites-available/telegram-bot.conf
```

Убедитесь, что в конфигурации есть следующие строки:

```nginx
# Включаем типы MIME
include /etc/nginx/mime.types;
default_type application/octet-stream;

# Явно указываем MIME-типы для HTML и CSS
types {
    text/html html htm;
    text/css css;
    application/javascript js;
}

# Основной маршрут для статических файлов
location / {
    try_files $uri $uri/ /index.html;
    add_header Content-Type text/html;
}

# Явно указываем обработку HTML-файлов
location ~ \.html$ {
    add_header Content-Type text/html;
}
```

### 2. Проверьте содержимое файлов

```bash
sudo cat /opt/SOKbot/public/index.html
sudo cat /opt/SOKbot/public/test.html
```

### 3. Проверьте права доступа

```bash
sudo ls -la /opt/SOKbot/public/
```

Убедитесь, что файлы принадлежат пользователю www-data и имеют права 644:

```bash
sudo chown www-data:www-data /opt/SOKbot/public/*.html
sudo chmod 644 /opt/SOKbot/public/*.html
```

### 4. Перезапустите Nginx

```bash
sudo systemctl restart nginx
```

### 5. Проверьте логи Nginx

```bash
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

## Проверка заголовков ответа

Для проверки заголовков ответа выполните:

```bash
curl -I https://srgolubev.ru
curl -I https://srgolubev.ru/test.html
```

В ответе должен быть заголовок `Content-Type: text/html`.
