# Инструкция по применению скрипта на сервере с доменом

Для того чтобы применить скрипт с правками на сервере с доменом (95.163.234.54), выполните следующие шаги:

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
chmod +x scripts/fix_html_display_issue.sh
```

## 4. Запустите скрипт с правами root

```bash
sudo ./scripts/fix_html_display_issue.sh
```

Скрипт автоматически выполнит следующие действия:
- Проверит и исправит конфигурацию Nginx
- Настроит MIME-типы
- Создаст тестовую страницу
- Проверит SSL-сертификаты
- Исправит права доступа к файлам
- Перезапустит Nginx

## 5. Проверьте результат

После выполнения скрипта проверьте, что страница отображается корректно:

```bash
curl -k https://srgolubev.ru
```

Также откройте в браузере:
- https://srgolubev.ru
- https://srgolubev.ru/test.html

## 6. Проверьте логи Nginx при необходимости

```bash
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

## Дополнительно: Проверка вебхука

Для проверки работоспособности вебхука выполните:

```bash
curl -k https://srgolubev.ru/webhook
```

Должен вернуться статус 200 или 405 (Method Not Allowed).

## Устранение возможных проблем

Если после выполнения скрипта страница все еще не отображается:

1. Проверьте, что директория `/opt/SOKbot/public` существует и содержит файл `index.html`:
   ```bash
   ls -la /opt/SOKbot/public
   ```

2. Проверьте права доступа:
   ```bash
   sudo chown -R www-data:www-data /opt/SOKbot/public
   sudo chmod -R 755 /opt/SOKbot/public
   ```

3. Проверьте конфигурацию Nginx:
   ```bash
   sudo nginx -t
   ```

4. Перезапустите Nginx вручную:
   ```bash
   sudo systemctl restart nginx
   ```

5. Проверьте статус Nginx:
   ```bash
   sudo systemctl status nginx
   ```
