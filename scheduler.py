#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import requests
import json
import time
from datetime import datetime, timedelta
import pytz

# API настройки для cron-job.org
CRONJOB_API_KEY = os.environ.get('CRONJOB_API_KEY')
CRONJOB_BASE_URL = 'https://api.cron-job.org'

# URL для вызова вашего бота
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
GITHUB_TOKEN = os.environ.get('GH_TOKEN')

def validate_environment():
    """Проверяет настройки переменных окружения"""
    if not CRONJOB_API_KEY:
        print("❌ Не установлена переменная CRONJOB_API_KEY")
        return False
    
    if not WEBHOOK_URL:
        print("❌ Не установлена переменная WEBHOOK_URL")
        return False
    
    if not GITHUB_TOKEN:
        print("❌ Не установлена переменная GH_TOKEN")
        return False
    
    print("✅ Все переменные окружения настроены")
    return True

def create_precise_notification_job(notification_time: datetime, title: str = None, retry_count: int = 3):
    """
    Создает точное задание в cron-job.org для указанного времени с улучшенной обработкой rate limiting
    """
    if not validate_environment():
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
                'event_type': 'floating_island_notification',
                'client_payload': {
                    'notification_time': notification_time.isoformat(),
                    'precision': 'exact'
                }
            })
        }
    }
    
    # Повторяем попытки при rate limiting с увеличенными паузами
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
                print(f"✅ Точное задание создано! Job ID: {job_id}")
                print(f"🕐 Время: {notification_time.strftime('%d.%m.%Y %H:%M')} UTC")
                return job_id
            elif response.status_code == 429:
                # Rate limiting - увеличиваем время ожидания прогрессивно
                wait_time = (attempt + 1) * 30  # 30, 60, 90 секунд
                print(f"⏳ Rate limit (попытка {attempt + 1}/{retry_count}). Ждем {wait_time} сек...")
                time.sleep(wait_time)
                continue
            elif response.status_code == 401:
                print(f"❌ Ошибка аутентификации cron-job.org. Проверьте API ключ")
                return False
            elif response.status_code == 400:
                print(f"❌ Некорректные данные запроса: {response.text}")
                return False
            else:
                print(f"❌ Ошибка создания задания: {response.status_code}")
                print(f"Ответ: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print(f"⏰ Таймаут запроса (попытка {attempt + 1}/{retry_count})")
            if attempt < retry_count - 1:
                time.sleep(10)
                continue
        except Exception as e:
            print(f"❌ Исключение при создании задания (попытка {attempt + 1}): {e}")
            if attempt < retry_count - 1:
                time.sleep(5)
                continue
            return False
    
    print(f"❌ Не удалось создать задание после {retry_count} попыток")
    return False

def cleanup_old_jobs():
    """
    Удаляет старые задания Floating Island из cron-job.org с улучшенной логикой
    """
    if not validate_environment():
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
        now = datetime.now(pytz.UTC)
        
        print(f"📋 Найдено {len(jobs)} заданий. Анализируем...")
        
        for job in jobs:
            title = job.get('title', '')
            job_id = job.get('jobId')
            
            # Ищем только задания Floating Island
            if 'Floating Island' in title and job_id:
                # Проверяем, не является ли это основным заданием (Checker)
                if 'Checker' in title or 'Notifications Checker' in title:
                    print(f"⚠️ Пропускаем основное задание: {title}")
                    continue
                
                # Удаляем конкретные задания (они одноразовые)
                try:
                    delete_response = requests.delete(
                        f"{CRONJOB_BASE_URL}/jobs/{job_id}",
                        headers=headers,
                        timeout=30
                    )
                    
                    if delete_response.status_code == 200:
                        print(f"🗑️ Удалено задание: {title} (ID: {job_id})")
                        deleted_count += 1
                    else:
                        print(f"⚠️ Не удалось удалить задание {job_id}: {delete_response.status_code}")
                        
                except Exception as e:
                    print(f"⚠️ Ошибка удаления задания {job_id}: {e}")
                
                # Пауза между удалениями чтобы избежать rate limiting
                time.sleep(2)
        
        print(f"✅ Очистка завершена. Удалено {deleted_count} заданий")
        return True
        
    except Exception as e:
        print(f"❌ Исключение при очистке заданий: {e}")
        return False

def schedule_floating_island_sequence(start_date: datetime = None, count: int = 30):
    """
    Планирует последовательность уведомлений Floating Island с улучшенной обработкой
    """
    try:
        from floating_island_bot import calculate_next_events
    except ImportError:
        print("❌ Не удалось импортировать floating_island_bot")
        return False
    
    if not validate_environment():
        return False
    
    if not start_date:
        start_date = datetime.now(pytz.UTC)
    
    print(f"📅 Планируем {count} уведомлений Floating Island")
    print(f"⏰ Начиная с: {start_date.strftime('%d.%m.%Y %H:%M')} UTC")
    print("=" * 60)
    
    # Начальная пауза для предотвращения rate limiting
    print("⏳ Начальная пауза 10 секунд...")
    time.sleep(10)
    
    # Сначала очищаем старые задания
    print("🧹 Очищаем старые задания...")
    cleanup_old_jobs()
    print()
    
    # Получаем события для планирования
    events = calculate_next_events(start_date, count=count)
    
    scheduled_count = 0
    failed_count = 0
    skipped_count = 0
    
    print(f"📊 Обрабатываем {len(events)} событий...")
    print("-" * 60)
    
    for i, event in enumerate(events, 1):
        notification_time = event['notification_time']
        event_start = event['event_start']
        
        # Пропускаем события в прошлом
        if notification_time <= start_date:
            print(f"⏭️ Событие {i}: пропускаем (в прошлом)")
            skipped_count += 1
            continue
        
        print(f"\n📌 Планируем событие {i}/{len(events)}:")
        print(f"   📢 Уведомление: {notification_time.strftime('%d.%m.%Y %H:%M')} UTC")
        print(f"   🎈 Событие: {event_start.strftime('%d.%m.%Y %H:%M')} UTC")
        
        # Вычисляем время до уведомления
        time_until = (notification_time - start_date).total_seconds()
        hours_until = int(time_until // 3600)
        print(f"   ⏰ Через: {hours_until} часов")
        
        title = f"Floating Island {notification_time.strftime('%d.%m %H:%M')} UTC"
        job_id = create_precise_notification_job(notification_time, title)
        
        if job_id:
            scheduled_count += 1
            print(f"   ✅ Запланировано (Job ID: {job_id})")
        else:
            failed_count += 1
            print(f"   ❌ Ошибка планирования")
        
        # Прогрессивная пауза между запросами для избежания rate limiting
        if i < len(events) and i % 5 == 0:
            # Большая пауза каждые 5 заданий
            print(f"   ⏸️ Пауза 60 секунд (каждые 5 заданий)...")
            time.sleep(60)
        elif i < len(events):
            # Обычная пауза
            time.sleep(20)  # Увеличиваем паузу до 20 секунд
    
    print(f"\n" + "=" * 60)
    print(f"📊 ИТОГИ ПЛАНИРОВАНИЯ:")
    print(f"✅ Успешно запланировано: {scheduled_count}")
    print(f"❌ Ошибок: {failed_count}")
    print(f"⏭️ Пропущено (прошлые): {skipped_count}")
    print(f"📋 Обработано событий: {len(events)}")
    
    if scheduled_count > 0:
        print(f"\n🎉 Система готова к работе!")
        print(f"📱 Уведомления будут отправляться автоматически")
        return True
    else:
        print(f"\n⚠️ Не удалось запланировать ни одного события")
        return False

def get_scheduled_jobs():
    """
    Показывает все запланированные задания Floating Island с улучшенным форматированием
    """
    if not validate_environment():
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
            print("=" * 80)
            
            # Разделяем на категории
            checker_jobs = []
            scheduled_jobs = []
            
            for job in floating_jobs:
                if 'Checker' in job.get('title', ''):
                    checker_jobs.append(job)
                else:
                    scheduled_jobs.append(job)
            
            # Показываем основные задания
            if checker_jobs:
                print("🔄 ОСНОВНЫЕ ЗАДАНИЯ (постоянные):")
                for job in checker_jobs:
                    job_id = job.get('jobId')
                    title = job.get('title', 'Без названия')
                    enabled = job.get('enabled', False)
                    
                    status = "🟢 Активно" if enabled else "🔴 Отключено"
                    print(f"  {status} {title} (ID: {job_id})")
                print()
            
            # Показываем запланированные уведомления
            if scheduled_jobs:
                print("📅 ЗАПЛАНИРОВАННЫЕ УВЕДОМЛЕНИЯ:")
                
                # Сортируем по времени
                now = datetime.now(pytz.UTC)
                scheduled_jobs.sort(key=lambda x: x.get('title', ''))
                
                for job in scheduled_jobs[:10]:  # Показываем первые 10
                    job_id = job.get('jobId')
                    title = job.get('title', 'Без названия')
                    enabled = job.get('enabled', False)
                    
                    status = "🟢" if enabled else "🔴"
                    print(f"  {status} {title} (ID: {job_id})")
                
                if len(scheduled_jobs) > 10:
                    print(f"  ... и еще {len(scheduled_jobs) - 10} заданий")
            
            print(f"\n📊 ВСЕГО: {len(floating_jobs)} заданий")
            
        elif response.status_code == 401:
            print("❌ Неверный API ключ cron-job.org")
        else:
            print(f"❌ Ошибка получения списка: {response.status_code}")
            print(f"Ответ: {response.text}")
            
    except Exception as e:
        print(f"❌ Исключение при получении списка: {e}")

def main():
    """Основная функция с CLI интерфейсом"""
    if len(sys.argv) < 2:
        print("📅 SCHEDULER - Планировщик заданий Floating Island")
        print("=" * 50)
        print("Использование:")
        print("  python scheduler.py schedule [количество]  - запланировать события (по умолчанию 30)")
        print("  python scheduler.py list                   - показать запланированные задания")
        print("  python scheduler.py cleanup                - очистить старые задания")
        print("  python scheduler.py test                   - тестировать подключения")
        print()
        print("Примеры:")
        print("  python scheduler.py schedule 50    # Запланировать 50 событий")
        print("  python scheduler.py schedule       # Запланировать 30 событий")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'schedule':
        count = 30
        if len(sys.argv) > 2:
            try:
                count = int(sys.argv[2])
                if count <= 0 or count > 100:
                    print("❌ Количество должно быть от 1 до 100")
                    return
            except ValueError:
                print("❌ Некорректное количество. Используйте число от 1 до 100")
                return
        
        print(f"🚀 Запускаем планирование {count} событий...")
        schedule_floating_island_sequence(count=count)
        
    elif command == 'list':
        get_scheduled_jobs()
        
    elif command == 'cleanup':
        print("🧹 Запускаем очистку старых заданий...")
        cleanup_old_jobs()
        
    elif command == 'test':
        print("🔧 ТЕСТИРОВАНИЕ СИСТЕМЫ")
        print("=" * 50)
        if validate_environment():
            try:
                from setup_cronjob import test_cronjob_connection, test_github_connection
                test_cronjob_connection()
                test_github_connection()
            except ImportError:
                print("⚠️ Модуль setup_cronjob недоступен для тестирования")
        
    else:
        print("❌ Неизвестная команда. Используйте: schedule, list, cleanup, test")

if __name__ == "__main__":
    main()
