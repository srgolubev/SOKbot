#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для проверки работоспособности веб-сайта и вебхука
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime

import requests
from colorama import Fore, Style, init

# Инициализация colorama
init()

# Константы
DEFAULT_DOMAIN = "srgolubev.ru"
DEFAULT_BOT_SERVER = "212.224.118.58"
DEFAULT_PORT = 8000


def print_colored(text, color=Fore.GREEN, bold=False):
    """Вывод цветного текста в консоль"""
    if bold:
        print(f"{color}{Style.BRIGHT}{text}{Style.RESET_ALL}")
    else:
        print(f"{color}{text}{Style.RESET_ALL}")


def check_website(domain, verbose=False):
    """Проверка доступности веб-сайта"""
    url = f"https://{domain}"
    try:
        start_time = time.time()
        response = requests.get(url, timeout=10)
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            print_colored(f"✅ Веб-сайт {url} доступен (статус {response.status_code})", Fore.GREEN, True)
            print_colored(f"   Время ответа: {elapsed_time:.2f} секунд", Fore.GREEN)
            
            if verbose:
                content_type = response.headers.get('Content-Type', '')
                print_colored(f"   Content-Type: {content_type}", Fore.CYAN)
                print_colored(f"   Размер ответа: {len(response.content)} байт", Fore.CYAN)
                
                # Проверка на наличие HTML-контента
                if 'text/html' in content_type:
                    if '<html' in response.text.lower():
                        print_colored(f"   HTML-контент обнаружен ✓", Fore.GREEN)
                    else:
                        print_colored(f"   ⚠️ HTML-тег не найден в ответе", Fore.YELLOW)
            
            return True
        else:
            print_colored(f"❌ Веб-сайт {url} вернул статус {response.status_code}", Fore.RED, True)
            return False
    except requests.exceptions.RequestException as e:
        print_colored(f"❌ Ошибка при подключении к {url}: {str(e)}", Fore.RED, True)
        return False


def check_test_page(domain, verbose=False):
    """Проверка тестовой страницы"""
    url = f"https://{domain}/test.html"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print_colored(f"✅ Тестовая страница {url} доступна", Fore.GREEN, True)
            
            if verbose and 'text/html' in response.headers.get('Content-Type', ''):
                if 'Тестовая страница' in response.text:
                    print_colored(f"   Контент тестовой страницы корректен ✓", Fore.GREEN)
                else:
                    print_colored(f"   ⚠️ Ожидаемый контент не найден", Fore.YELLOW)
            
            return True
        else:
            print_colored(f"❌ Тестовая страница {url} вернула статус {response.status_code}", Fore.RED, True)
            return False
    except requests.exceptions.RequestException as e:
        print_colored(f"❌ Ошибка при подключении к {url}: {str(e)}", Fore.RED, True)
        return False


def check_webhook_endpoint(domain, verbose=False):
    """Проверка доступности эндпоинта вебхука"""
    url = f"https://{domain}/webhook"
    try:
        response = requests.get(url, timeout=10)
        # Вебхук может возвращать 405 Method Not Allowed для GET-запросов, это нормально
        if response.status_code in [200, 404, 405]:
            print_colored(f"✅ Эндпоинт вебхука {url} доступен (статус {response.status_code})", Fore.GREEN, True)
            if verbose:
                print_colored(f"   Примечание: статус 405 для GET-запроса к вебхуку - это нормально", Fore.CYAN)
            return True
        else:
            print_colored(f"❌ Эндпоинт вебхука {url} вернул неожиданный статус {response.status_code}", Fore.RED, True)
            return False
    except requests.exceptions.RequestException as e:
        print_colored(f"❌ Ошибка при подключении к {url}: {str(e)}", Fore.RED, True)
        return False


def check_health_endpoint(domain=None, bot_server=None, port=None, verbose=False):
    """Проверка эндпоинта проверки здоровья"""
    if domain:
        url = f"https://{domain}/health"
    elif bot_server:
        url = f"http://{bot_server}:{port}/health"
    else:
        print_colored("❌ Не указан ни домен, ни сервер бота", Fore.RED, True)
        return False
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print_colored(f"✅ Эндпоинт проверки здоровья {url} доступен", Fore.GREEN, True)
            
            try:
                health_data = response.json()
                if verbose:
                    print_colored("   Данные о состоянии системы:", Fore.CYAN)
                    print(json.dumps(health_data, indent=4, ensure_ascii=False))
                
                status = health_data.get('status', 'unknown')
                if status == 'ok':
                    print_colored(f"   Статус системы: {status} ✓", Fore.GREEN)
                else:
                    print_colored(f"   ⚠️ Статус системы: {status}", Fore.YELLOW)
            except json.JSONDecodeError:
                print_colored(f"   ⚠️ Ответ не является валидным JSON", Fore.YELLOW)
            
            return True
        else:
            print_colored(f"❌ Эндпоинт проверки здоровья {url} вернул статус {response.status_code}", Fore.RED, True)
            return False
    except requests.exceptions.RequestException as e:
        print_colored(f"❌ Ошибка при подключении к {url}: {str(e)}", Fore.RED, True)
        return False


def check_direct_bot_server(bot_server, port, verbose=False):
    """Проверка прямого подключения к серверу бота"""
    url = f"http://{bot_server}:{port}/health"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print_colored(f"✅ Сервер бота {url} доступен напрямую", Fore.GREEN, True)
            return True
        else:
            print_colored(f"❌ Сервер бота {url} вернул статус {response.status_code}", Fore.RED, True)
            return False
    except requests.exceptions.RequestException as e:
        print_colored(f"❌ Ошибка при прямом подключении к серверу бота {url}: {str(e)}", Fore.RED, True)
        return False


def main():
    parser = argparse.ArgumentParser(description="Проверка работоспособности веб-сайта и вебхука")
    parser.add_argument("-d", "--domain", default=DEFAULT_DOMAIN, help=f"Домен для проверки (по умолчанию: {DEFAULT_DOMAIN})")
    parser.add_argument("-b", "--bot-server", default=DEFAULT_BOT_SERVER, help=f"IP-адрес сервера с ботом (по умолчанию: {DEFAULT_BOT_SERVER})")
    parser.add_argument("-p", "--port", type=int, default=DEFAULT_PORT, help=f"Порт сервера с ботом (по умолчанию: {DEFAULT_PORT})")
    parser.add_argument("-v", "--verbose", action="store_true", help="Подробный вывод")
    parser.add_argument("--skip-website", action="store_true", help="Пропустить проверку веб-сайта")
    parser.add_argument("--skip-test-page", action="store_true", help="Пропустить проверку тестовой страницы")
    parser.add_argument("--skip-webhook", action="store_true", help="Пропустить проверку вебхука")
    parser.add_argument("--skip-health", action="store_true", help="Пропустить проверку эндпоинта здоровья")
    parser.add_argument("--skip-direct", action="store_true", help="Пропустить прямую проверку сервера бота")
    
    args = parser.parse_args()
    
    print_colored(f"🔍 Начинаем проверку системы ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})", Fore.CYAN, True)
    print_colored(f"   Домен: {args.domain}", Fore.CYAN)
    print_colored(f"   Сервер бота: {args.bot_server}:{args.port}", Fore.CYAN)
    print("-" * 60)
    
    results = {}
    
    if not args.skip_website:
        results['website'] = check_website(args.domain, args.verbose)
        print("-" * 60)
    
    if not args.skip_test_page:
        results['test_page'] = check_test_page(args.domain, args.verbose)
        print("-" * 60)
    
    if not args.skip_webhook:
        results['webhook'] = check_webhook_endpoint(args.domain, args.verbose)
        print("-" * 60)
    
    if not args.skip_health:
        results['health'] = check_health_endpoint(args.domain, verbose=args.verbose)
        print("-" * 60)
    
    if not args.skip_direct:
        results['direct'] = check_direct_bot_server(args.bot_server, args.port, args.verbose)
        print("-" * 60)
    
    # Итоговый результат
    success_count = sum(1 for result in results.values() if result)
    total_count = len(results)
    
    if total_count > 0:
        success_rate = (success_count / total_count) * 100
        print_colored(f"📊 Итоговый результат: {success_count}/{total_count} проверок успешно ({success_rate:.1f}%)", 
                     Fore.GREEN if success_rate == 100 else Fore.YELLOW if success_rate >= 50 else Fore.RED, 
                     True)
    else:
        print_colored("❗ Не выполнено ни одной проверки", Fore.YELLOW, True)
    
    # Возвращаем код ошибки, если хотя бы одна проверка не прошла
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
