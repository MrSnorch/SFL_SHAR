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
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')

# Настройки Telegram для прямого тестирования
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def validate_environment():
    """Проверяет настройки переменных окружения"""
    missing = []
    
    if not FASTCRON_API_KEY:
        missing.append("FASTCRON_API_KEY")
    if not WEBHOOK_URL:
        missing.append("WEBHOOK_URL") 
    if not GITHUB_TOKEN:
        missing.append("GITHUB_TOKEN")
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_CHAT_ID:
        missing.append("TELEGRAM_CHAT_ID")
    
    if missing:
        print(f"❌ Отсутствуют переменные: {', '.join(missing)}")
        return False
    
    print("✅ Все переменные окружения настроены")
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
    
    # Формируем тестовое сообщение согласно спецификации
    message = f"""🏝️ ЕБУЧИЙ ШАР прибыл!

⏰ Доступен сейчас:
   🇺🇦 Киев: {now_kyiv.strftime('%H:%M')} ({now_kyiv.strftime('%d.%m')})
   🌍 UTC: {now_utc.strftime('%H:%M')} ({now_utc.strftime('%d.%m')})

⏳ Продолжительность: 30 минут
   (до {(now_kyiv + timedelta(minutes=30)).strftime('%H:%M')} по Киеву)

🧪 ТЕСТОВОЕ УВЕДОМЛЕНИЕ
Следующее прибытие в {next_kyiv.strftime('%H:%M')}"""

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
    
    # Подготавливаем данные для GitHub webhook
    post_data = json.dumps({
        'event_type': 'floating_island_notification',
        'client_payload': {
            'notification_time': test_time.isoformat(),
            'precision': 'test',
            'test_mode': True
        }
    })
    
    # HTTP заголовки для GitHub API
    http_headers = f"Authorization: token {GITHUB_TOKEN}\\r\\nAccept: application/vnd.github.v3+json\\r\\nContent-Type: application/json"
    
    # Параметры для FastCron API
    params = {
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
        response = requests.get(
            f"{FASTCRON_BASE_URL}/v1/cron_add",
            params=params,
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

def create_test_github_webhook():
    """Создает тестовый webhook напрямую в GitHub для немедленного выполнения"""
    if not WEBHOOK_URL or not GITHUB_TOKEN:
        print("❌ Нет данных для GitHub webhook")
        return False
    
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }
    
    test_payload = {
        'event_type': 'floating_island_notification',
        'client_payload': {
            'notification_time': datetime.now(pytz.UTC).isoformat(),
            'precision': 'test_immediate',
            'test_mode': True
        }
    }
    
    try:
        print("🚀 Отправляем тестовый webhook в GitHub...")
        response = requests.post(WEBHOOK_URL, headers=headers, json=test_payload, timeout=10)
        
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