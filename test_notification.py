#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import requests
import json
import time
from datetime import datetime, timedelta
import pytz

# Настройки для FastCron.com
FASTCRON_API_KEY = os.environ.get('FASTCRON_API_KEY')
FASTCRON_BASE_URL = 'https://www.fastcron.com/api'

# URL для вызова бота
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
GITHUB_TOKEN = os.environ.get('GH_TOKEN')

# Настройки Telegram для прямого тестирования
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def validate_webhook_url(url):
    """Проверяет правильность формата webhook URL"""
    if not url:
        return False, "URL не задан"
    
    if not url.startswith('https://api.github.com/repos/'):
        return False, "URL должен начинаться с https://api.github.com/repos/"
    
    if not url.endswith('/dispatches'):
        return False, "URL должен заканчиваться на /dispatches"
    
    # Проверяем структуру URL
    parts = url.replace('https://api.github.com/repos/', '').replace('/dispatches', '').split('/')
    if len(parts) != 2 or not all(parts):
        return False, "Неправильный формат. Должно быть: https://api.github.com/repos/{owner}/{repo}/dispatches"
    
    return True, f"Правильный формат: владелец={parts[0]}, репозиторий={parts[1]}"

def validate_environment():
    """Проверяет настройки переменных окружения"""
    missing = []
    errors = []
    
    if not FASTCRON_API_KEY:
        missing.append("FASTCRON_API_KEY")
    if not WEBHOOK_URL:
        missing.append("WEBHOOK_URL") 
    if not GITHUB_TOKEN:
        missing.append("GH_TOKEN")
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_CHAT_ID:
        missing.append("TELEGRAM_CHAT_ID")
    
    if missing:
        errors.append(f"❌ Отсутствуют переменные: {', '.join(missing)}")
    
    # Проверяем формат WEBHOOK_URL
    if WEBHOOK_URL:
        is_valid, message = validate_webhook_url(WEBHOOK_URL)
        if not is_valid:
            errors.append(f"❌ Ошибка WEBHOOK_URL: {message}")
    
    if errors:
        print("\n".join(errors))
        print("\n💡 Инструкции по настройке:")
        print("1. FASTCRON_API_KEY - API ключ с сайта fastcron.com")
        print("2. WEBHOOK_URL - https://api.github.com/repos/{username}/{repo}/dispatches")
        print("3. GH_TOKEN - Personal Access Token с правами 'repo' и 'workflow'")
        print("4. TELEGRAM_BOT_TOKEN - Токен Telegram бота")
        print("5. TELEGRAM_CHAT_ID - ID чата для уведомлений")
        return False
    
    print("✅ Все переменные окружения настроены")
    if WEBHOOK_URL:
        is_valid, message = validate_webhook_url(WEBHOOK_URL)
        print(f"🔗 WEBHOOK_URL: {message}")
    return True

def send_test_telegram_message():
    """Отправляет тестовое уведомление напрямую в Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Нет токена Telegram или chat ID для прямой отправки")
        return False
    
    # Текущее время для тестирования
    now_utc = datetime.now(pytz.UTC)
    kyiv_tz = pytz.timezone('Europe/Kiev')
    now_kyiv = now_utc.astimezone(kyiv_tz)
    
    # Следующее появление через 8 часов 20 минут (для теста)
    next_event = now_utc + timedelta(hours=8, minutes=20)
    next_kyiv = next_event.astimezone(kyiv_tz)
    
    # Формируем тестовое сообщение в новом формате
    message = f"""ЕБУЧИЙ ШАР прибыл!
Следующие прибытие: {next_kyiv.strftime('%H:%M')}

🧪 ТЕСТОВОЕ УВЕДОМЛЕНИЕ"""

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    data = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        print(f"📱 Отправляем тестовое сообщение в чат {TELEGRAM_CHAT_ID}...")
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            print("✅ Тестовое уведомление отправлено в Telegram!")
            print(f"📄 Сообщение:\n{message}")
            return True
        else:
            print(f"❌ Ошибка отправки в Telegram: {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Исключение при отправке в Telegram: {e}")
        return False

def create_test_github_webhook():
    """Создает тестовый webhook напрямую в GitHub для немедленного выполнения"""
    if not WEBHOOK_URL or not GITHUB_TOKEN:
        print("❌ Нет данных для GitHub webhook")
        return False
    
    # Извлекаем owner и repo из WEBHOOK_URL для формирования правильного URL
    try:
        if WEBHOOK_URL.startswith('https://api.github.com/repos/'):
            url_parts = WEBHOOK_URL.replace('https://api.github.com/repos/', '').split('/')
            if len(url_parts) >= 2:
                owner, repo = url_parts[0], url_parts[1]
                # Новый формат URL для dispatches
                github_dispatch_url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/184853159/dispatches"
            else:
                print("❌ Неправильный формат WEBHOOK_URL")
                return False
        else:
            print("❌ WEBHOOK_URL должен начинаться с https://api.github.com/repos/")
            return False
    except Exception as e:
        print(f"❌ Ошибка разбора WEBHOOK_URL: {e}")
        return False
    
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }
    
    # Правильный формат payload для workflow dispatches - только разрешенные параметры
    test_payload = {
        'ref': 'main',  # Обязательное поле
        'inputs': {
            'action': 'test-send'
        }
    }
    
    try:
        print("🚀 Отправляем тестовый webhook в GitHub...")
        response = requests.post(github_dispatch_url, headers=headers, json=test_payload, timeout=10)
        
        if response.status_code == 204:
            print("✅ Тестовый webhook отправлен в GitHub!")
            print("📋 GitHub Actions должен запуститься через несколько секунд")
            return True
        else:
            print(f"❌ Ошибка GitHub webhook: {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Исключение при отправке webhook: {e}")
        return False

def create_test_fastcron_job():
    """Создает тестовое задание в FastCron на выполнение через 30 секунд"""
    if not validate_environment():
        return False
    
    # Вычисляем время через 30 секунд
    test_time = datetime.now(pytz.UTC) + timedelta(seconds=30)
    
    minute = test_time.minute
    hour = test_time.hour
    day = test_time.day
    month = test_time.month
    
    cron_expression = f"{minute} {hour} {day} {month} *"
    
    print(f"🧪 СОЗДАНИЕ ТЕСТОВОГО ЗАДАНИЯ")
    print(f"⏰ Запуск через 30 секунд: {test_time.strftime('%H:%M:%S')} UTC")
    print(f"⚙️ Cron выражение: {cron_expression}")
    
    title = f"TEST Floating Island {test_time.strftime('%d.%m %H:%M')} UTC"
    
    # Подготавливаем данные для GitHub webhook (новый формат)
    post_data = json.dumps({
        "event_type": "floating_island_notification",
        "client_payload": {
            "notification_time": test_time.isoformat(),
            "precision": "test",
            "test_mode": True
        },
        "ref": "main"
    })
    
    # HTTP заголовки для GitHub API
    http_headers = f"Authorization: token {GITHUB_TOKEN}\\r\\nAccept: application/vnd.github.v3+json\\r\\nContent-Type: application/json"
    
    # Параметры для FastCron API (используем POST с правильным форматом)
    payload = {
        'token': FASTCRON_API_KEY,
        'name': title,
        'expression': cron_expression,
        'url': WEBHOOK_URL,
        'httpMethod': 'POST',
        'postData': post_data,
        'httpHeaders': http_headers,
        'timezone': 'UTC',
        'notify': 'false'
    }
    
    try:
        response = requests.post(
            f"{FASTCRON_BASE_URL}/v1/cron_add",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                job_data = result.get('data', {})
                job_id = job_data.get('id')
                print(f"✅ Тестовое задание создано в FastCron (ID: {job_id})")
                print(f"🕐 Задание выполнится в: {test_time.strftime('%H:%M:%S')} UTC")
                return job_id
            else:
                error_msg = result.get('message', 'Неизвестная ошибка')
                print(f"❌ Ошибка FastCron: {error_msg}")
                return False
        else:
            print(f"❌ Ошибка HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Исключение при создании тестового задания: {e}")
        return False

def main():
    """Основная функция тестирования"""
    if len(sys.argv) < 2:
        print("🧪 TEST NOTIFICATION - Тестирование уведомлений")
        print("=" * 55)
        print("Использование:")
        print("  python test_notification.py telegram    - прямая отправка в Telegram")
        print("  python test_notification.py fastcron    - тест через FastCron (30 сек)")
        print("  python test_notification.py github      - тест через GitHub webhook")
        print("  python test_notification.py full        - полное тестирование")
        print()
        print("Примеры:")
        print("  python test_notification.py telegram    # Быстрый тест")
        print("  python test_notification.py fastcron    # Тест планировщика")
        print("  python test_notification.py full        # Все тесты")
        return
    
    command = sys.argv[1].lower()
    
    print(f"🧪 ТЕСТИРОВАНИЕ СИСТЕМЫ УВЕДОМЛЕНИЙ")
    print(f"⏰ Время запуска: {datetime.now(pytz.UTC).strftime('%H:%M:%S')} UTC")
    print("=" * 60)
    
    if command == 'telegram':
        print("📱 ПРЯМОЙ ТЕСТ TELEGRAM")
        send_test_telegram_message()
        
    elif command == 'fastcron':
        print("⚡ ТЕСТ ЧЕРЕЗ FASTCRON (30 СЕКУНД)")
        job_id = create_test_fastcron_job()
        if job_id:
            print(f"✅ Задание создано! Ожидайте уведомление через 30 секунд")
            print(f"🕐 Следите за GitHub Actions и Telegram")
        
    elif command == 'github':
        print("🚀 ТЕСТ ЧЕРЕЗ GITHUB WEBHOOK")
        create_test_github_webhook()
        
    elif command == 'full':
        print("🔄 ПОЛНОЕ ТЕСТИРОВАНИЕ")
        print("\n1️⃣ Тест прямой отправки в Telegram...")
        send_test_telegram_message()
        
        print("\n2️⃣ Тест GitHub webhook...")
        create_test_github_webhook()
        
        print("\n3️⃣ Тест FastCron планировщика...")
        job_id = create_test_fastcron_job()
        if job_id:
            print(f"✅ Все тесты запущены!")
            print(f"📱 Ожидайте уведомления в течение 1 минуты")
        
    else:
        print("❌ Неизвестная команда. Используйте: telegram, fastcron, github, full")

if __name__ == "__main__":
    main()