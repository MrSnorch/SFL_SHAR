#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import requests
import json
import time
from datetime import datetime, timedelta
import pytz

# API настройки для FastCron.com
FASTCRON_API_KEY = os.environ.get('FASTCRON_API_KEY')
FASTCRON_BASE_URL = 'https://www.fastcron.com/api'

# URL для вызова вашего бота
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
GITHUB_TOKEN = os.environ.get('GH_TOKEN')

def validate_environment():
    """Проверяет настройки переменных окружения"""
    if not FASTCRON_API_KEY:
        print("❌ Не установлена переменная FASTCRON_API_KEY")
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
    Создает точное задание в FastCron для указанного времени
    FastCron имеет более мягкие ограничения по rate limiting
    """
    if not validate_environment():
        return False
    
    # FastCron использует стандартный cron формат
    minute = notification_time.minute
    hour = notification_time.hour
    day = notification_time.day
    month = notification_time.month
    
    cron_expression = f"{minute} {hour} {day} {month} *"
    
    if not title:
        title = f"Floating Island {notification_time.strftime('%d.%m %H:%M')} UTC"
    
    job_data = {
        'token': FASTCRON_API_KEY,
        'name': title,
        'cron': cron_expression,
        'url': WEBHOOK_URL,
        'method': 'POST',
        'headers': json.dumps([
            f"Authorization: token {GITHUB_TOKEN}",
            "Accept: application/vnd.github.v3+json",
            "Content-Type: application/json"
        ]),
        'data': json.dumps({
            'event_type': 'floating_island_notification',
            'client_payload': {
                'notification_time': notification_time.isoformat(),
                'precision': 'exact'
            }
        }),
        'timezone': 'UTC'
    }
    
    # FastCron более терпим к частым запросам
    for attempt in range(retry_count):
        try:
            response = requests.post(
                f"{FASTCRON_BASE_URL}/crontab",
                data=job_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'OK':
                    job_id = result.get('id')
                    print(f"✅ FastCron задание создано! Job ID: {job_id}")
                    print(f"🕐 Время: {notification_time.strftime('%d.%m.%Y %H:%M')} UTC")
                    print(f"⚙️ Cron: {cron_expression}")
                    return job_id
                else:
                    print(f"❌ Ошибка FastCron: {result.get('message', 'Неизвестная ошибка')}")
                    return False
            elif response.status_code == 429:
                # FastCron rate limiting - более мягкое
                wait_time = (attempt + 1) * 3  # 3, 6, 9 секунд (намного меньше чем у cron-job.org)
                print(f"⏳ FastCron rate limit (попытка {attempt + 1}/{retry_count}). Ждем {wait_time} сек...")
                time.sleep(wait_time)
                continue
            else:
                print(f"❌ Ошибка HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print(f"⏰ Таймаут запроса (попытка {attempt + 1}/{retry_count})")
            if attempt < retry_count - 1:
                time.sleep(2)
                continue
        except Exception as e:
            print(f"❌ Исключение (попытка {attempt + 1}): {e}")
            if attempt < retry_count - 1:
                time.sleep(2)
                continue
            return False
    
    print(f"❌ Не удалось создать FastCron задание после {retry_count} попыток")
    return False

def cleanup_old_jobs():
    """
    Удаляет старые задания Floating Island из FastCron
    """
    if not validate_environment():
        return False
    
    try:
        # Получаем список всех заданий
        response = requests.get(
            f"{FASTCRON_BASE_URL}/crontab",
            params={'token': FASTCRON_API_KEY},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Ошибка получения списка FastCron заданий: {response.status_code}")
            return False
        
        result = response.json()
        if result.get('status') != 'OK':
            print(f"❌ FastCron API ошибка: {result.get('message')}")
            return False
        
        crons = result.get('crons', [])
        deleted_count = 0
        
        print(f"📋 Найдено {len(crons)} заданий. Анализируем...")
        
        for cron in crons:
            name = cron.get('name', '')
            job_id = cron.get('id')
            
            # Ищем только задания Floating Island
            if 'Floating Island' in name and job_id:
                # Проверяем, не является ли это основным заданием (Checker)
                if 'Checker' in name or 'Notifications Checker' in name:
                    print(f"⚠️ Пропускаем основное задание: {name}")
                    continue
                
                # Удаляем конкретные задания (они одноразовые)
                try:
                    delete_response = requests.delete(
                        f"{FASTCRON_BASE_URL}/crontab/{job_id}",
                        params={'token': FASTCRON_API_KEY},
                        timeout=30
                    )
                    
                    if delete_response.status_code == 200:
                        delete_result = delete_response.json()
                        if delete_result.get('status') == 'OK':
                            print(f"🗑️ Удалено задание: {name} (ID: {job_id})")
                            deleted_count += 1
                        else:
                            print(f"⚠️ Не удалось удалить задание {job_id}: {delete_result.get('message')}")
                    else:
                        print(f"⚠️ HTTP ошибка при удалении {job_id}: {delete_response.status_code}")
                        
                except Exception as e:
                    print(f"⚠️ Исключение при удалении задания {job_id}: {e}")
                
                # Минимальная пауза между удалениями для FastCron
                time.sleep(1)
        
        print(f"✅ Очистка завершена. Удалено {deleted_count} заданий")
        return True
        
    except Exception as e:
        print(f"❌ Исключение при очистке заданий: {e}")
        return False

def schedule_floating_island_sequence(start_date: datetime = None, count: int = 30):
    """
    Планирует последовательность уведомлений Floating Island в FastCron
    FastCron имеет более высокие лимиты, поэтому можем планировать быстрее
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
    
    print(f"📅 Планируем {count} уведомлений Floating Island через FastCron")
    print(f"⏰ Начиная с: {start_date.strftime('%d.%m.%Y %H:%M')} UTC")
    print("=" * 60)
    
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
            print(f"   ✅ Запланировано (FastCron ID: {job_id})")
        else:
            failed_count += 1
            print(f"   ❌ Ошибка планирования")
        
        # FastCron более терпим - можем использовать короткие паузы
        if i < len(events) and i % 10 == 0:
            # Пауза каждые 10 заданий
            print(f"   ⏸️ Пауза 5 секунд (каждые 10 заданий)...")
            time.sleep(5)
        elif i < len(events):
            # Короткая пауза между запросами
            time.sleep(2)  # Всего 2 секунды вместо 20!
    
    print(f"\n" + "=" * 60)
    print(f"📊 ИТОГИ ПЛАНИРОВАНИЯ FASTCRON:")
    print(f"✅ Успешно запланировано: {scheduled_count}")
    print(f"❌ Ошибок: {failed_count}")
    print(f"⏭️ Пропущено (прошлые): {skipped_count}")
    print(f"📋 Обработано событий: {len(events)}")
    
    if scheduled_count > 0:
        print(f"\n🎉 FastCron система готова к работе!")
        print(f"📱 Уведомления будут отправляться автоматически")
        print(f"💡 FastCron: более быстрое планирование, меньше ограничений")
        return True
    else:
        print(f"\n⚠️ Не удалось запланировать ни одного события")
        return False

def get_scheduled_jobs():
    """
    Показывает все запланированные задания FastCron Floating Island
    """
    if not validate_environment():
        return
    
    try:
        response = requests.get(
            f"{FASTCRON_BASE_URL}/crontab",
            params={'token': FASTCRON_API_KEY},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'OK':
                crons = result.get('crons', [])
                floating_jobs = [cron for cron in crons if 'Floating Island' in cron.get('name', '')]
                
                if not floating_jobs:
                    print("📭 Нет запланированных заданий Floating Island в FastCron")
                    return
                
                print(f"📋 Найдено {len(floating_jobs)} заданий Floating Island в FastCron:")
                print("=" * 80)
                
                # Разделяем на категории
                checker_jobs = []
                scheduled_jobs = []
                
                for job in floating_jobs:
                    if 'Checker' in job.get('name', ''):
                        checker_jobs.append(job)
                    else:
                        scheduled_jobs.append(job)
                
                # Показываем основные задания
                if checker_jobs:
                    print("🔄 ОСНОВНЫЕ ЗАДАНИЯ (постоянные):")
                    for job in checker_jobs:
                        job_id = job.get('id')
                        name = job.get('name', 'Без названия')
                        status = job.get('status', 0)
                        cron_expr = job.get('cron', '')
                        
                        status_text = "🟢 Активно" if status == 1 else "🔴 Отключено"
                        print(f"  {status_text} {name} (ID: {job_id})")
                        print(f"    Cron: {cron_expr}")
                    print()
                
                # Показываем запланированные уведомления
                if scheduled_jobs:
                    print("📅 ЗАПЛАНИРОВАННЫЕ УВЕДОМЛЕНИЯ:")
                    
                    # Сортируем по названию (содержит время)
                    scheduled_jobs.sort(key=lambda x: x.get('name', ''))
                    
                    for job in scheduled_jobs[:15]:  # Показываем первые 15
                        job_id = job.get('id')
                        name = job.get('name', 'Без названия')
                        status = job.get('status', 0)
                        cron_expr = job.get('cron', '')
                        
                        status_text = "🟢" if status == 1 else "🔴"
                        print(f"  {status_text} {name} (ID: {job_id})")
                        print(f"    Cron: {cron_expr}")
                    
                    if len(scheduled_jobs) > 15:
                        print(f"  ... и еще {len(scheduled_jobs) - 15} заданий")
                
                print(f"\n📊 ВСЕГО FASTCRON: {len(floating_jobs)} заданий")
                print(f"💡 FastCron имеет более высокие лимиты чем cron-job.org")
            else:
                print(f"❌ FastCron API ошибка: {result.get('message')}")
        else:
            print(f"❌ Ошибка HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Исключение при получении списка: {e}")

def main():
    """Основная функция с CLI интерфейсом для FastCron"""
    if len(sys.argv) < 2:
        print("📅 FASTCRON SCHEDULER - Планировщик заданий Floating Island")
        print("=" * 60)
        print("Использование:")
        print("  python fastcron_scheduler.py schedule [количество]  - запланировать события")
        print("  python fastcron_scheduler.py list                   - показать задания")
        print("  python fastcron_scheduler.py cleanup                - очистить старые")
        print("  python fastcron_scheduler.py test                   - тестировать")
        print()
        print("Преимущества FastCron:")
        print("• Более высокие лимиты API")
        print("• Быстрое планирование (паузы 2 сек вместо 20)")
        print("• Мягкое rate limiting")
        print("• Надежная доставка")
        print()
        print("Примеры:")
        print("  python fastcron_scheduler.py schedule 50    # Запланировать 50 событий")
        print("  python fastcron_scheduler.py schedule       # Запланировать 30 событий")
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
        
        print(f"🚀 Запускаем FastCron планирование {count} событий...")
        schedule_floating_island_sequence(count=count)
        
    elif command == 'list':
        get_scheduled_jobs()
        
    elif command == 'cleanup':
        print("🧹 Запускаем очистку старых FastCron заданий...")
        cleanup_old_jobs()
        
    elif command == 'test':
        print("🔧 ТЕСТИРОВАНИЕ FASTCRON СИСТЕМЫ")
        print("=" * 50)
        if validate_environment():
            try:
                from setup_fastcron import test_fastcron_connection, test_github_connection
                test_fastcron_connection()
                test_github_connection()
            except ImportError:
                print("⚠️ Модуль setup_fastcron недоступен для тестирования")
        
    else:
        print("❌ Неизвестная команда. Используйте: schedule, list, cleanup, test")

if __name__ == "__main__":
    main()