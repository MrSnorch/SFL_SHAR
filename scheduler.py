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

# URL для вызова вашего бота
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')

def create_precise_notification_job(notification_time: datetime, title: str = None):
    """
    Создает точное задание в cron-job.org для указанного времени
    """
    if not CRONJOB_API_KEY:
        print("❌ Не установлена переменная CRONJOB_API_KEY")
        return False
    
    if not WEBHOOK_URL:
        print("❌ Не установлена переменная WEBHOOK_URL")
        return False
    
    # Форматируем время для cron-job.org
    minute = notification_time.minute
    hour = notification_time.hour
    day = notification_time.day
    month = notification_time.month
    
    if not title:
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
                'wdays': [-1]  # любой день недели
            },
            'requestMethod': 1,  # POST
            'requestHeaders': [
                {
                    'name': 'Content-Type',
                    'value': 'application/json'
                },
                {
                    'name': 'X-Notification-Type',
                    'value': 'floating-island-precise'
                }
            ],
            'requestBody': json.dumps({
                'event_type': 'floating_island_notification',
                'client_payload': {
                    'notification_time': notification_time.isoformat(),
                    'precision': 'exact'
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
            print(f"✅ Точное задание создано! Job ID: {job_id}")
            print(f"🕐 Время: {notification_time.strftime('%d.%m.%Y %H:%M')} UTC")
            return job_id
        else:
            print(f"❌ Ошибка создания задания: {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Исключение при создании задания: {e}")
        return False

def cleanup_old_jobs():
    """
    Удаляет старые задания Floating Island из cron-job.org
    """
    if not CRONJOB_API_KEY:
        print("❌ Не установлена переменная CRONJOB_API_KEY")
        return False
    
    headers = {
        'Authorization': f'Bearer {CRONJOB_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Получаем список всех заданий
        response = requests.get(f"{CRONJOB_BASE_URL}/jobs", headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Ошибка получения списка заданий: {response.status_code}")
            return False
        
        jobs = response.json().get('jobs', [])
        deleted_count = 0
        
        for job in jobs:
            title = job.get('title', '')
            job_id = job.get('jobId')
            
            # Ищем задания Floating Island
            if 'Floating Island' in title and job_id:
                # Удаляем все старые задания (они уже выполнились или неактуальны)
                try:
                    delete_response = requests.delete(
                        f"{CRONJOB_BASE_URL}/jobs/{job_id}",
                        headers=headers,
                        timeout=30
                    )
                    
                    if delete_response.status_code == 200:
                        print(f"🗑️ Удалено старое задание: {title} (ID: {job_id})")
                        deleted_count += 1
                    else:
                        print(f"⚠️ Не удалось удалить задание {job_id}: {delete_response.status_code}")
                        
                except Exception as e:
                    print(f"⚠️ Ошибка удаления задания {job_id}: {e}")
        
        print(f"✅ Очистка завершена. Удалено {deleted_count} старых заданий")
        return True
        
    except Exception as e:
        print(f"❌ Исключение при очистке заданий: {e}")
        return False

def schedule_floating_island_sequence(start_date: datetime = None, count: int = 30):
    """
    Планирует последовательность уведомлений Floating Island
    """
    from floating_island_bot import calculate_next_events
    
    if not start_date:
        start_date = datetime.now(pytz.UTC)
    
    print(f"📅 Планируем {count} уведомлений Floating Island, начиная с {start_date.strftime('%d.%m.%Y %H:%M')} UTC")
    
    # Сначала очищаем старые задания
    print("🧹 Очищаем старые задания...")
    cleanup_old_jobs()
    
    # Получаем события для планирования
    events = calculate_next_events(start_date, count=count)
    
    scheduled_count = 0
    failed_count = 0
    
    for i, event in enumerate(events, 1):
        notification_time = event['notification_time']
        event_start = event['event_start']
        
        # Пропускаем события в прошлом
        if notification_time <= start_date:
            continue
        
        print(f"\n📌 Планируем событие {i}:")
        print(f"   Уведомление: {notification_time.strftime('%d.%m.%Y %H:%M')} UTC")
        print(f"   Событие: {event_start.strftime('%d.%m.%Y %H:%M')} UTC")
        
        title = f"Floating Island {notification_time.strftime('%d.%m %H:%M')} UTC"
        job_id = create_precise_notification_job(notification_time, title)
        
        if job_id:
            scheduled_count += 1
            print(f"   ✅ Запланировано (Job ID: {job_id})")
        else:
            failed_count += 1
            print(f"   ❌ Ошибка планирования")
    
    print(f"\n📊 ИТОГИ ПЛАНИРОВАНИЯ:")
    print(f"✅ Успешно запланировано: {scheduled_count}")
    print(f"❌ Ошибок: {failed_count}")
    print(f"📋 Всего событий: {scheduled_count + failed_count}")
    
    return scheduled_count > 0

def get_scheduled_jobs():
    """
    Показывает все запланированные задания Floating Island
    """
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
            floating_jobs = [job for job in jobs if 'Floating Island' in job.get('title', '')]
            
            if not floating_jobs:
                print("📭 Нет запланированных заданий Floating Island")
                return
            
            print(f"📋 Найдено {len(floating_jobs)} заданий Floating Island:")
            print("-" * 60)
            
            for job in floating_jobs:
                job_id = job.get('jobId')
                title = job.get('title', 'Без названия')
                enabled = job.get('enabled', False)
                
                status = "🟢 Активно" if enabled else "🔴 Отключено"
                print(f"{status} {title} (ID: {job_id})")
                
        else:
            print(f"❌ Ошибка получения списка: {response.status_code}")
            print(f"Ответ: {response.text}")
            
    except Exception as e:
        print(f"❌ Исключение при получении списка: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("🤖 ПЛАНИРОВЩИК FLOATING ISLAND")
        print("=" * 40)
        print("Доступные команды:")
        print("  python scheduler.py schedule [count] - Запланировать уведомления (по умолчанию 30)")
        print("  python scheduler.py list             - Показать запланированные задания")
        print("  python scheduler.py cleanup          - Очистить старые задания")
        print("  python scheduler.py single DATETIME  - Запланировать одно уведомление")
        print("")
        print("Примеры:")
        print("  python scheduler.py schedule 10")
        print("  python scheduler.py single '2025-08-28 22:00'")
    else:
        command = sys.argv[1].lower()
        
        if command == 'schedule':
            count = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            schedule_floating_island_sequence(count=count)
        elif command == 'list':
            get_scheduled_jobs()
        elif command == 'cleanup':
            cleanup_old_jobs()
        elif command == 'single' and len(sys.argv) > 2:
            datetime_str = sys.argv[2]
            try:
                dt = datetime.fromisoformat(datetime_str.replace(' ', 'T')).replace(tzinfo=pytz.UTC)
                create_precise_notification_job(dt)
            except ValueError:
                print("❌ Неверный формат даты. Используйте: 'YYYY-MM-DD HH:MM'")
        else:
            print("❌ Неизвестная команда")