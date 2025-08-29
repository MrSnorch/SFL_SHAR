#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Альтернативный планировщик для создания одного задания за раз
Используется когда основной планировщик сталкивается с rate limiting
"""

import os
import sys
from datetime import datetime, timedelta
import pytz

# Импортируем функции из основных модулей
try:
    from floating_island_bot import calculate_next_events
    from setup_cronjob import create_single_notification_job, validate_environment
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("💡 Убедитесь, что файлы floating_island_bot.py и setup_cronjob.py находятся в той же папке")
    sys.exit(1)

def schedule_single_event():
    """Планирует только одно следующее событие"""
    if not validate_environment():
        return False
    
    now = datetime.now(pytz.UTC)
    events = calculate_next_events(now, count=1)
    
    if not events:
        print("❌ Не найдено событий для планирования")
        return False
    
    event = events[0]
    notification_time = event['notification_time']
    
    # Пропускаем события в прошлом
    if notification_time <= now:
        print("⏭️ Пропускаем событие в прошлом, ищем следующее...")
        events = calculate_next_events(now + timedelta(minutes=1), count=1)
        if events:
            event = events[0]
            notification_time = event['notification_time']
        else:
            print("❌ Не найдено будущих событий")
            return False
    
    event_start = event['event_start']
    
    print(f"🎯 ПЛАНИРОВАНИЕ ОДНОГО СОБЫТИЯ")
    print("=" * 50)
    print(f"📢 Уведомление: {notification_time.strftime('%d.%m.%Y %H:%M')} UTC")
    print(f"🎈 Событие: {event_start.strftime('%d.%m.%Y %H:%M')} UTC")
    
    # Вычисляем время до события
    time_until = (notification_time - now).total_seconds()
    hours_until = int(time_until // 3600)
    print(f"⏰ Через: {hours_until} часов")
    
    title = f"Floating Island {notification_time.strftime('%d.%m %H:%M')} UTC"
    
    print(f"\n🚀 Создаем задание...")
    job_id = create_single_notification_job(notification_time, title)
    
    if job_id:
        print(f"✅ Событие успешно запланировано!")
        print(f"🆔 Job ID: {job_id}")
        print(f"\n💡 Для планирования следующего события запустите:")
        print(f"   python single_scheduler.py")
        return True
    else:
        print(f"❌ Не удалось запланировать событие")
        return False

def show_next_event():
    """Показывает информацию о следующем событии"""
    now = datetime.now(pytz.UTC)
    events = calculate_next_events(now, count=1)
    
    if not events:
        print("❌ Не найдено событий")
        return
    
    event = events[0]
    notification_time = event['notification_time']
    event_start = event['event_start']
    
    kiev_tz = pytz.timezone('Europe/Kiev')
    event_kiev = event_start.astimezone(kiev_tz)
    
    print(f"📅 СЛЕДУЮЩЕЕ СОБЫТИЕ")
    print("=" * 30)
    print(f"🎈 Floating Island: {event_kiev.strftime('%d.%m.%Y %H:%M')} (Киев)")
    print(f"📢 Уведомление: {notification_time.strftime('%d.%m.%Y %H:%M')} UTC")
    
    time_until = (notification_time - now).total_seconds()
    if time_until > 0:
        hours = int(time_until // 3600)
        minutes = int((time_until % 3600) // 60)
        print(f"⏰ До уведомления: {hours}ч {minutes}мин")
    else:
        print(f"⚠️ Событие уже прошло")

def main():
    """Основная функция"""
    if len(sys.argv) > 1 and sys.argv[1] == 'info':
        show_next_event()
        return
    
    print(f"🤖 ОДИНОЧНЫЙ ПЛАНИРОВЩИК FLOATING ISLAND")
    print(f"⏰ Время: {datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print()
    
    if schedule_single_event():
        print(f"\n🎉 Готово! Система будет автоматически отправлять уведомления.")
    else:
        print(f"\n💡 Попробуйте позже или проверьте настройки API.")

if __name__ == "__main__":
    main()