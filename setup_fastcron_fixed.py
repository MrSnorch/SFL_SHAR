#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json
import time
from datetime import datetime, timedelta
import pytz

# API настройки для FastCron.com
FASTCRON_API_KEY = os.environ.get('FASTCRON_API_KEY')
FASTCRON_BASE_URL = 'https://app.fastcron.com/api'

# URL для вызова вашего бота (через GitHub Actions)
# Формат: https://api.github.com/repos/{owner}/{repo}/dispatches
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')

def validate_environment():
    """Проверяет настройки переменных окружения"""
    errors = []
    
    if not FASTCRON_API_KEY:
        errors.append("❌ Не установлена переменная FASTCRON_API_KEY")
    
    if not WEBHOOK_URL:
        errors.append("❌ Не установлена переменная WEBHOOK_URL")
    elif not WEBHOOK_URL.startswith('https://api.github.com/repos/'):
        errors.append("❌ WEBHOOK_URL должен быть GitHub API URL: https://api.github.com/repos/{owner}/{repo}/dispatches")
    
    if not GITHUB_TOKEN:
        errors.append("❌ Не установлена переменная GITHUB_TOKEN")
    
    if errors:
        print("\n".join(errors))
        print("\n💡 Инструкции по настройке:")
        print("1. FASTCRON_API_KEY - API ключ с сайта fastcron.com")
        print("2. WEBHOOK_URL - https://api.github.com/repos/{username}/{repo}/dispatches")
        print("3. GITHUB_TOKEN - Personal Access Token с правами 'repo' и 'workflow'")
        return False
    
    return True

def test_fastcron_connection():
    """Тестирует подключение к FastCron API"""
    if not FASTCRON_API_KEY:
        return False
    
    try:
        # Используем правильный эндпоинт FastCron
        response = requests.get(
            f"{FASTCRON_BASE_URL}/v1/cron_list",
            params={'token': FASTCRON_API_KEY},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                print("✅ Подключение к FastCron API успешно")
                crons = data.get('data', [])
                print(f"📊 Найдено {len(crons)} активных заданий")
                return True
            else:
                print(f"❌ Ошибка FastCron API: {data.get('message', 'Неизвестная ошибка')}")
                return False
        elif response.status_code == 401:
            print("❌ Неверный API ключ FastCron")
            return False
        else:
            print(f"⚠️ Проблема с подключением к FastCron: {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения к FastCron: {e}")
        return False

def test_github_connection():
    """Тестирует подключение к GitHub API"""
    if not WEBHOOK_URL or not GITHUB_TOKEN:
        return False
    
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }
    
    test_payload = {
        'event_type': 'test_fastcron_connection',
        'client_payload': {
            'test': True,
            'timestamp': datetime.now(pytz.UTC).isoformat()
        }
    }
    
    try:
        response = requests.post(WEBHOOK_URL, headers=headers, json=test_payload, timeout=10)
        
        if response.status_code == 204:
            print("✅ Подключение к GitHub API успешно")
            return True
        elif response.status_code == 401:
            print("❌ Неверный GitHub токен")
            return False
        elif response.status_code == 404:
            print("❌ Неверный URL репозитория или нет прав доступа")
            return False
        else:
            print(f"⚠️ Проблема с подключением к GitHub: {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения к GitHub: {e}")
        return False

def create_single_notification_job(notification_time: datetime, retry_count: int = 3):
    """
    Создает одно точное задание для уведомления в указанное время в FastCron
    """
    if not validate_environment():
        return False
    
    # FastCron использует стандартный cron формат
    minute = notification_time.minute
    hour = notification_time.hour
    day = notification_time.day
    month = notification_time.month
    
    # Создаем cron выражение для конкретной даты/времени
    cron_expression = f"{minute} {hour} {day} {month} *"
    
    title = f"Floating Island {notification_time.strftime('%d.%m %H:%M')} UTC"
    
    # Подготавливаем POST данные для GitHub webhook
    post_data = json.dumps({
        'event_type': 'floating_island_notification',
        'client_payload': {
            'notification_time': notification_time.isoformat(),
            'auto_scheduled': True
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
        'notify': 'false'  # Отключаем уведомления о сбоях
    }
    
    for attempt in range(retry_count):
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
                    print(f"✅ FastCron задание создано (ID: {job_id})")
                    print(f"🕐 Время: {notification_time.strftime('%d.%m.%Y %H:%M')} UTC")
                    print(f"⚙️ Cron: {cron_expression}")
                    return job_id
                else:
                    error_msg = result.get('message', 'Неизвестная ошибка')
                    print(f"❌ Ошибка FastCron: {error_msg}")
                    return False
            elif response.status_code == 429:
                # Rate limiting - FastCron имеет более мягкие ограничения
                wait_time = (attempt + 1) * 5  # 5, 10, 15 секунд
                print(f"⏳ Rate limit FastCron (попытка {attempt + 1}/{retry_count}). Ждем {wait_time} сек...")
                time.sleep(wait_time)
                continue
            else:
                print(f"❌ Ошибка HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Исключение FastCron (попытка {attempt + 1}): {e}")
            if attempt < retry_count - 1:
                time.sleep(3)
                continue
            return False
    
    print(f"❌ Не удалось создать задание FastCron после {retry_count} попыток")
    return False

def create_fastcron_schedule():
    """
    Создает основное задание в FastCron для проверки событий каждые 20 минут
    """
    if not validate_environment():
        return False
    
    print("🔧 Тестируем подключения...")
    
    if not test_fastcron_connection():
        return False
    
    if not test_github_connection():
        return False
    
    # Подготавливаем POST данные для GitHub webhook
    post_data = json.dumps({
        'event_type': 'floating_island_check',
        'client_payload': {
            'type': 'periodic_check'
        }
    })
    
    # HTTP заголовки для GitHub API
    http_headers = f"Authorization: token {GITHUB_TOKEN}\\r\\nAccept: application/vnd.github.v3+json\\r\\nContent-Type: application/json"
    
    # Создаем задание, которое запускается каждые 20 минут
    params = {
        'token': FASTCRON_API_KEY,
        'name': 'Floating Island Notifications Checker',
        'expression': '0,20,40 * * * *',  # каждые 20 минут
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
                print(f"✅ Основное FastCron задание создано! Job ID: {job_id}")
                print(f"🔗 URL: {WEBHOOK_URL}")
                print(f"⏰ Расписание: каждые 20 минут (:00, :20, :40)")
                print(f"🔑 GitHub Token: {GITHUB_TOKEN[:10]}...{GITHUB_TOKEN[-4:]}")
                return True
            else:
                error_msg = result.get('message', 'Неизвестная ошибка')
                print(f"❌ Ошибка FastCron: {error_msg}")
                return False
        else:
            print(f"❌ Ошибка HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Исключение при создании FastCron задания: {e}")
        return False

def list_existing_jobs():
    """Показывает существующие задания FastCron"""
    if not FASTCRON_API_KEY:
        print("❌ Не установлена переменная FASTCRON_API_KEY")
        return
    
    try:
        response = requests.get(
            f"{FASTCRON_BASE_URL}/v1/cron_list",
            params={'token': FASTCRON_API_KEY},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                crons = result.get('data', [])
                print(f"📋 Найдено {len(crons)} заданий FastCron:")
                print("=" * 80)
                
                floating_jobs = []
                other_jobs = []
                
                for cron in crons:
                    if 'Floating Island' in cron.get('name', ''):
                        floating_jobs.append(cron)
                    else:
                        other_jobs.append(cron)
                
                if floating_jobs:
                    print(f"🏝️ Floating Island задания ({len(floating_jobs)}):")
                    for job in floating_jobs:
                        job_id = job.get('id')
                        name = job.get('name', 'Без названия')
                        status = job.get('status', 0)
                        expression = job.get('expression', '')
                        
                        status_text = "🟢 Активно" if status == 1 else "🔴 Отключено"
                        print(f"  {status_text} ID: {job_id} - {name}")
                        print(f"    Cron: {expression}")
                
                if other_jobs:
                    print(f"\n📌 Другие задания ({len(other_jobs)}):")
                    for job in other_jobs:
                        job_id = job.get('id')
                        name = job.get('name', 'Без названия')
                        status = job.get('status', 0)
                        
                        status_text = "🟢 Активно" if status == 1 else "🔴 Отключено"
                        print(f"  {status_text} ID: {job_id} - {name}")
            else:
                error_msg = result.get('message', 'Неизвестная ошибка')
                print(f"❌ Ошибка FastCron: {error_msg}")
        else:
            print(f"❌ Ошибка HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Исключение при получении списка: {e}")

def delete_job(job_id: str):
    """Удаляет задание FastCron по ID"""
    if not FASTCRON_API_KEY:
        print("❌ Не установлена переменная FASTCRON_API_KEY")
        return False
    
    try:
        response = requests.get(
            f"{FASTCRON_BASE_URL}/v1/cron_delete",
            params={
                'token': FASTCRON_API_KEY,
                'id': job_id
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                print(f"✅ FastCron задание {job_id} удалено успешно")
                return True
            else:
                error_msg = result.get('message', 'Неизвестная ошибка')
                print(f"❌ Ошибка FastCron: {error_msg}")
                return False
        else:
            print(f"❌ Ошибка HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Исключение при удалении задания: {e}")
        return False

def main():
    """Основная функция с CLI интерфейсом для FastCron"""
    import sys
    
    if len(sys.argv) < 2:
        print("🔧 SETUP FASTCRON - Управление заданиями FastCron.com")
        print("=" * 50)
        print("Использование:")
        print("  python setup_fastcron_fixed.py list        - показать все задания")
        print("  python setup_fastcron_fixed.py create      - создать основное задание")
        print("  python setup_fastcron_fixed.py delete <ID> - удалить задание по ID")
        print("  python setup_fastcron_fixed.py test        - тестировать подключения")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'list':
        list_existing_jobs()
    elif command == 'create':
        create_fastcron_schedule()
    elif command == 'delete' and len(sys.argv) > 2:
        job_id = sys.argv[2]
        delete_job(job_id)
    elif command == 'test':
        print("🔧 ТЕСТИРОВАНИЕ FASTCRON ПОДКЛЮЧЕНИЙ")
        print("=" * 50)
        validate_environment()
        test_fastcron_connection()
        test_github_connection()
    else:
        print("❌ Неизвестная команда. Используйте: list, create, delete <ID>, test")

if __name__ == "__main__":
    main()