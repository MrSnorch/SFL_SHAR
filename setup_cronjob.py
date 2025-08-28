#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json
from datetime import datetime, timedelta
import pytz

# API настройки для cron-job.org
CRONJOB_API_KEY = os.environ.get('CRONJOB_API_KEY')
CRONJOB_BASE_URL = 'https://api.cron-job.org'

# URL для вызова вашего бота (через GitHub Actions или другой webhook)
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')  # Например: https://api.github.com/repos/username/repo/dispatches

def create_single_notification_job(notification_time: datetime):
    """
    Создает одно точное задание для уведомления в указанное время
    """
    if not CRONJOB_API_KEY:
        print("❌ Не установлена переменная CRONJOB_API_KEY")
        return False
    
    if not WEBHOOK_URL:
        print("❌ Не установлена переменная WEBHOOK_URL")
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
            'requestMethod': 1,
            'requestHeaders': [
                {
                    'name': 'Content-Type',
                    'value': 'application/json'
                },
                {
                    'name': 'X-Notification-Type',
                    'value': 'floating-island-auto'
                }
            ],
            'requestBody': json.dumps({
                'event_type': 'floating_island_notification',
                'client_payload': {
                    'notification_time': notification_time.isoformat(),
                    'auto_scheduled': True
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
            print(f"✅ Автопланирование: задание создано (ID: {job_id})")
            return job_id
        else:
            print(f"❌ Ошибка автопланирования: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Исключение автопланирования: {e}")
        return False

def create_cronjob_schedule():
    """
    Создает задания в cron-job.org для точного времени уведомлений
    Использует интервал каждые 20 минут для покрытия всех возможных времен
    """
    
    if not CRONJOB_API_KEY:
        print("❌ Не установлена переменная CRONJOB_API_KEY")
        return False
    
    if not WEBHOOK_URL:
        print("❌ Не установлена переменная WEBHOOK_URL")
        return False
    
    headers = {
        'Authorization': f'Bearer {CRONJOB_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Создаем задание, которое запускается каждые 20 минут
    # Это обеспечит точность уведомлений в пределах 20 минут
    job_data = {
        'job': {
            'url': WEBHOOK_URL,
            'enabled': True,
            'title': 'Floating Island Notifications',
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
                    'name': 'Content-Type',
                    'value': 'application/json'
                }
            ],
            'requestBody': json.dumps({
                'event_type': 'floating_island_check',
                'client_payload': {}
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
            print(f"✅ Задание создано успешно! Job ID: {job_id}")
            print(f"🔗 URL: {WEBHOOK_URL}")
            print(f"⏰ Расписание: каждые 20 минут (:00, :20, :40)")
            return True
        else:
            print(f"❌ Ошибка создания задания: {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Исключение при создании задания: {e}")
        return False

def list_existing_jobs():
    """Показывает существующие задания"""
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
            
            for job in jobs:
                job_id = job.get('jobId')
                title = job.get('title', 'Без названия')
                enabled = job.get('enabled', False)
                url = job.get('url', '')
                
                status = "🟢 Активно" if enabled else "🔴 Отключено"
                print(f"  {status} ID: {job_id} - {title}")
                print(f"    URL: {url}")
                
        else:
            print(f"❌ Ошибка получения списка: {response.status_code}")
            print(f"Ответ: {response.text}")
            
    except Exception as e:
        print(f"❌ Исключение при получении списка: {e}")

def delete_job(job_id: str):
    """Удаляет задание по ID"""
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
        else:
            print(f"❌ Ошибка удаления задания: {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Исключение при удалении задания: {e}")
        return False

def setup_github_webhook():
    """
    Инструкции по настройке GitHub webhook для работы с cron-job.org
    """
    print("🔧 НАСТРОЙКА GITHUB WEBHOOK")
    print("=" * 50)
    print()
    print("1. Создайте GitHub Personal Access Token:")
    print("   - Перейдите в Settings → Developer settings → Personal access tokens")
    print("   - Создайте токен с правами 'repo' и 'workflow'")
    print("   - Сохраните токен как переменную окружения GITHUB_TOKEN")
    print()
    print("2. Создайте workflow файл .github/workflows/floating-island.yml:")
    print()
    
    workflow_content = """name: Floating Island Notifications

on:
  repository_dispatch:
    types: [floating_island_check]
  workflow_dispatch:

jobs:
  notify:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.11

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install requests pytz

      - name: Run floating island bot
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: |
          echo "=== FLOATING ISLAND CHECK ==="
          python floating_island_bot.py
          echo "=== END CHECK ==="
"""
    
    print(workflow_content)
    print()
    print("3. Добавьте секреты в GitHub:")
    print("   - TELEGRAM_BOT_TOKEN: токен вашего Telegram бота")
    print("   - TELEGRAM_CHAT_ID: ID чата для уведомлений")
    print()
    print("4. URL для webhook будет:")
    print("   https://api.github.com/repos/USERNAME/REPOSITORY/dispatches")
    print("   (замените USERNAME и REPOSITORY на ваши)")
    print()
    print("5. Установите переменные окружения:")
    print("   - CRONJOB_API_KEY: ключ API от cron-job.org")
    print("   - WEBHOOK_URL: URL из пункта 4")

def main():
    """Основная функция меню"""
    import sys
    
    if len(sys.argv) < 2:
        print("🤖 НАСТРОЙКА CRON-JOB.ORG ДЛЯ FLOATING ISLAND")
        print("=" * 50)
        print("Доступные команды:")
        print("  python setup_cronjob.py create    - Создать новое задание")
        print("  python setup_cronjob.py list      - Показать существующие задания")
        print("  python setup_cronjob.py delete ID - Удалить задание по ID")
        print("  python setup_cronjob.py setup     - Инструкции по настройке")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'create':
        create_cronjob_schedule()
    elif command == 'list':
        list_existing_jobs()
    elif command == 'delete' and len(sys.argv) > 2:
        job_id = sys.argv[2]
        delete_job(job_id)
    elif command == 'setup':
        setup_github_webhook()
    else:
        print("❌ Неизвестная команда. Используйте: create, list, delete, setup")

if __name__ == "__main__":
    main()