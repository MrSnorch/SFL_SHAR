#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json
import time
from datetime import datetime, timedelta
import pytz

# API настройки для cron-job.org
CRONJOB_API_KEY = os.environ.get('CRONJOB_API_KEY')
CRONJOB_BASE_URL = 'https://api.cron-job.org'

# URL для вызова вашего бота (через GitHub Actions)
# Формат: https://api.github.com/repos/{owner}/{repo}/dispatches
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
GITHUB_TOKEN = os.environ.get('GH_TOKEN')

def validate_environment():
    """Проверяет настройки переменных окружения"""
    errors = []
    
    if not CRONJOB_API_KEY:
        errors.append("❌ Не установлена переменная CRONJOB_API_KEY")
    
    if not WEBHOOK_URL:
        errors.append("❌ Не установлена переменная WEBHOOK_URL")
    elif not WEBHOOK_URL.startswith('https://api.github.com/repos/'):
        errors.append("❌ WEBHOOK_URL должен быть GitHub API URL: https://api.github.com/repos/{owner}/{repo}/dispatches")
    
    if not GITHUB_TOKEN:
        errors.append("❌ Не установлена переменная GH_TOKEN")
    
    if errors:
        print("\n".join(errors))
        print("\n💡 Инструкции по настройке:")
        print("1. CRONJOB_API_KEY - API ключ с сайта cron-job.org")
        print("2. WEBHOOK_URL - https://api.github.com/repos/{username}/{repo}/dispatches")
        print("3. GH_TOKEN - Personal Access Token с правами 'repo' и 'workflow'")
        return False
    
    return True

def test_cronjob_connection():
    """Тестирует подключение к cron-job.org API"""
    if not CRONJOB_API_KEY:
        return False
    
    headers = {
        'Authorization': f'Bearer {CRONJOB_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{CRONJOB_BASE_URL}/jobs", headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ Подключение к cron-job.org API успешно")
            return True
        elif response.status_code == 401:
            print("❌ Неверный API ключ cron-job.org")
            return False
        else:
            print(f"⚠️ Проблема с подключением к cron-job.org: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения к cron-job.org: {e}")
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
        'event_type': 'test_connection',
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
    Создает одно точное задание для уведомления в указанное время
    С улучшенной обработкой rate limiting и ошибок
    """
    if not validate_environment():
        return False
    
    # Форматируем время для cron
    minute = notification_time.minute
    hour = notification_time.hour
    day = notification_time.day
    month = notification_time.month
    
    title = f"Floating Island {notification_time.strftime('%d.%m %H:%M')} UTC"
    
    headers = {
        'Authorization': f'Bearer {CRONJOB_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    job_data = {
        'job': {
            'url': WEBHOOK_URL,
            'enabled': True,
            'title': title,
            'schedule': {
                'timezone': 'UTC',
                'hours': [hour],
                'minutes': [minute],
                'mdays': [day],
                'months': [month],
                'wdays': [-1]
            },
            'requestMethod': 1,  # POST
            'requestHeaders': [
                {
                    'name': 'Authorization',
                    'value': f'token {GITHUB_TOKEN}'
                },
                {
                    'name': 'Accept',
                    'value': 'application/vnd.github.v3+json'
                },
                {
                    'name': 'Content-Type',
                    'value': 'application/json'
                }
            ],
            'requestBody': json.dumps({
                'ref': 'main',
                'inputs': {
                    'action': 'notify'
                }
            })
        }
    }
    
    for attempt in range(retry_count):
        try:
            response = requests.put(
                f"{CRONJOB_BASE_URL}/jobs",
                headers=headers,
                json=job_data,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                job_id = result.get('jobId')
                print(f"✅ Автопланирование: задание создано (ID: {job_id})")
                print(f"🕐 Время: {notification_time.strftime('%d.%m.%Y %H:%M')} UTC")
                return job_id
            elif response.status_code == 429:
                # Rate limiting - увеличиваем время ожидания
                wait_time = (attempt + 1) * 25  # 25, 50, 75 секунд
                print(f"⏳ Rate limit (попытка {attempt + 1}/{retry_count}). Ждем {wait_time} сек...")
                time.sleep(wait_time)
                continue
            elif response.status_code == 401:
                print(f"❌ Ошибка аутентификации cron-job.org. Проверьте API ключ")
                return False
            else:
                print(f"❌ Ошибка автопланирования: {response.status_code}")
                print(f"Ответ: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Исключение автопланирования (попытка {attempt + 1}): {e}")
            if attempt < retry_count - 1:
                time.sleep(5)
                continue
            return False
    
    print(f"❌ Не удалось создать задание после {retry_count} попыток")
    return False

def create_cronjob_schedule():
    """
    Создает задания в cron-job.org для точного времени уведомлений
    Использует интервал каждые 20 минут для покрытия всех возможных времен
    """
    
    if not validate_environment():
        return False
    
    print("🔧 Тестируем подключения...")
    
    if not test_cronjob_connection():
        return False
    
    if not test_github_connection():
        return False
    
    headers = {
        'Authorization': f'Bearer {CRONJOB_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Создаем задание, которое запускается каждые 20 минут
    job_data = {
        'job': {
            'url': WEBHOOK_URL,
            'enabled': True,
            'title': 'Floating Island Notifications Checker',
            'schedule': {
                'timezone': 'UTC',
                'hours': [-1],  # каждый час
                'minutes': [0, 20, 40],  # каждые 20 минут
                'mdays': [-1],  # каждый день
                'months': [-1],  # каждый месяц
                'wdays': [-1]   # каждый день недели
            },
            'requestMethod': 1,  # POST
            'requestHeaders': [
                {
                    'name': 'Authorization',
                    'value': f'token {GITHUB_TOKEN}'
                },
                {
                    'name': 'Accept',
                    'value': 'application/vnd.github.v3+json'
                },
                {
                    'name': 'Content-Type',
                    'value': 'application/json'
                }
            ],
            'requestBody': json.dumps({
                'ref': 'main',
                'inputs': {
                    'action': 'notify',
                    'type': 'periodic_check'
                }
            })
        }
    }
    
    try:
        response = requests.put(
            f"{CRONJOB_BASE_URL}/jobs",
            headers=headers,
            json=job_data,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            job_id = result.get('jobId')
            print(f"✅ Основное задание создано успешно! Job ID: {job_id}")
            print(f"🔗 URL: {WEBHOOK_URL}")
            print(f"⏰ Расписание: каждые 20 минут (:00, :20, :40)")
            print(f"🔑 GitHub Token: {GITHUB_TOKEN[:10]}...{GITHUB_TOKEN[-4:]}")
            return True
        else:
            print(f"❌ Ошибка создания задания: {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Исключение при создании задания: {e}")
        return False

def list_existing_jobs():
    """Показывает существующие задания с улучшенным форматированием"""
    if not CRONJOB_API_KEY:
        print("❌ Не установлена переменная CRONJOB_API_KEY")
        return
    
    headers = {
        'Authorization': f'Bearer {CRONJOB_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{CRONJOB_BASE_URL}/jobs", headers=headers, timeout=30)
        
        if response.status_code == 200:
            jobs = response.json().get('jobs', [])
            print(f"📋 Найдено {len(jobs)} заданий:")
            print("=" * 80)
            
            floating_jobs = []
            other_jobs = []
            
            for job in jobs:
                if 'Floating Island' in job.get('title', ''):
                    floating_jobs.append(job)
                else:
                    other_jobs.append(job)
            
            if floating_jobs:
                print(f"🎈 Floating Island задания ({len(floating_jobs)}):")
                for job in floating_jobs:
                    job_id = job.get('jobId')
                    title = job.get('title', 'Без названия')
                    enabled = job.get('enabled', False)
                    
                    status = "🟢 Активно" if enabled else "🔴 Отключено"
                    print(f"  {status} ID: {job_id} - {title}")
            
            if other_jobs:
                print(f"\n📌 Другие задания ({len(other_jobs)}):")
                for job in other_jobs:
                    job_id = job.get('jobId')
                    title = job.get('title', 'Без названия')
                    enabled = job.get('enabled', False)
                    
                    status = "🟢 Активно" if enabled else "🔴 Отключено"
                    print(f"  {status} ID: {job_id} - {title}")
                
        elif response.status_code == 401:
            print("❌ Неверный API ключ cron-job.org")
        else:
            print(f"❌ Ошибка получения списка: {response.status_code}")
            print(f"Ответ: {response.text}")
            
    except Exception as e:
        print(f"❌ Исключение при получении списка: {e}")

def delete_job(job_id: str):
    """Удаляет задание по ID с подтверждением"""
    if not CRONJOB_API_KEY:
        print("❌ Не установлена переменная CRONJOB_API_KEY")
        return False
    
    headers = {
        'Authorization': f'Bearer {CRONJOB_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.delete(f"{CRONJOB_BASE_URL}/jobs/{job_id}", headers=headers, timeout=30)
        
        if response.status_code == 200:
            print(f"✅ Задание {job_id} удалено успешно")
            return True
        elif response.status_code == 404:
            print(f"❌ Задание {job_id} не найдено")
            return False
        else:
            print(f"❌ Ошибка удаления задания: {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Исключение при удалении задания: {e}")
        return False

def main():
    """Основная функция с CLI интерфейсом"""
    import sys
    
    if len(sys.argv) < 2:
        print("🔧 SETUP CRONJOB - Управление заданиями cron-job.org")
        print("=" * 50)
        print("Использование:")
        print("  python setup_cronjob.py list        - показать все задания")
        print("  python setup_cronjob.py create      - создать основное задание")
        print("  python setup_cronjob.py delete <ID> - удалить задание по ID")
        print("  python setup_cronjob.py test        - тестировать подключения")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'list':
        list_existing_jobs()
    elif command == 'create':
        create_cronjob_schedule()
    elif command == 'delete' and len(sys.argv) > 2:
        job_id = sys.argv[2]
        delete_job(job_id)
    elif command == 'test':
        print("🔧 ТЕСТИРОВАНИЕ ПОДКЛЮЧЕНИЙ")
        print("=" * 50)
        validate_environment()
        test_cronjob_connection()
        test_github_connection()
    else:
        print("❌ Неизвестная команда. Используйте: list, create, delete <ID>, test")

if __name__ == "__main__":
    main()