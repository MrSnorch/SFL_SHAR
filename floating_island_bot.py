#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import requests
import json
from datetime import datetime, timedelta
import pytz

# Константы для Telegram бота
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# Базовые настройки для расчета расписания Floating Island
# Первое событие: 19.08.2025 16:00 UTC (время появления острова)
BASE_EVENT_TIME = datetime(2025, 8, 19, 16, 0, 0, tzinfo=pytz.UTC)
EVENT_INTERVAL = timedelta(hours=8, minutes=20)  # Интервал между событиями
NOTIFICATION_ADVANCE = timedelta(minutes=0)  # Уведомление в момент появления острова
EVENT_DURATION = timedelta(minutes=30)  # Продолжительность события

# Настройки для webhook
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
GITHUB_TOKEN = os.environ.get('GH_TOKEN')

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

def get_github_dispatch_url(webhook_url):
    """Получает правильный URL для GitHub Actions dispatches"""
    if not webhook_url:
        return None
    
    try:
        if webhook_url.startswith('https://api.github.com/repos/'):
            url_parts = webhook_url.replace('https://api.github.com/repos/', '').split('/')
            if len(url_parts) >= 2:
                owner, repo = url_parts[0], url_parts[1]
                # Правильный формат URL для dispatches с конкретным workflow ID
                return f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/184853159/dispatches"
    except Exception as e:
        print(f"❌ Ошибка формирования GitHub dispatch URL: {e}")
        return None
    
    return None

def send_telegram_message(message: str, parse_mode: str = 'HTML'):
    """Отправляет сообщение в Telegram с улучшенной обработкой ошибок"""
    if not BOT_TOKEN or not CHAT_ID:
        print(f"⚠️ Не настроены переменные окружения для Telegram")
        print(f"BOT_TOKEN: {'✅ установлен' if BOT_TOKEN else '❌ не установлен'}")
        print(f"CHAT_ID: {'✅ установлен' if CHAT_ID else '❌ не установлен'}")
        print(f"Сообщение: {message}")
        return False
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': parse_mode
    }
    
    try:
        response = requests.post(url, json=payload, timeout=15)
        
        if response.status_code == 200:
            print(f"✅ Уведомление отправлено успешно")
            return True
        elif response.status_code == 400:
            # Попробуем без форматирования
            payload['parse_mode'] = None
            response = requests.post(url, json=payload, timeout=15)
            if response.status_code == 200:
                print(f"✅ Уведомление отправлено успешно (без форматирования)")
                return True
            else:
                print(f"❌ Ошибка отправки: {response.status_code} - {response.text}")
                return False
        else:
            print(f"❌ Ошибка отправки: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Исключение при отправке: {e}")
        return False

def calculate_next_events(from_time: datetime, count: int = 10):
    """Рассчитывает следующие события Floating Island"""
    events = []
    
    # Находим первое событие после заданного времени
    current_event = BASE_EVENT_TIME
    while current_event < from_time:
        current_event += EVENT_INTERVAL
    
    # Генерируем список событий
    for i in range(count):
        event_start = current_event
        event_end = event_start + EVENT_DURATION
        # Уведомление в момент начала события
        notification_time = event_start - NOTIFICATION_ADVANCE
        
        events.append({
            'notification_time': notification_time,
            'event_start': event_start,
            'event_end': event_end,
            'event_number': i + 1
        })
        
        current_event += EVENT_INTERVAL
    
    return events

def get_current_notification_event():
    """Получает событие, уведомление о котором должно быть отправлено сейчас (в пределах ±2 минут)"""
    now = datetime.now(pytz.UTC)
    tolerance = timedelta(minutes=5)  # Допуск ±5 минут
    
    print(f"🔍 Проверяем время появления острова: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    # Получаем события на ближайшие дни
    events = calculate_next_events(now - timedelta(days=1), count=100)
    
    for event in events:
        notification_time = event['notification_time']
        time_diff = abs((now - notification_time).total_seconds())
        
        if time_diff <= tolerance.total_seconds():
            print(f"✅ Найдено событие для уведомления: разница {time_diff:.0f} секунд")
            print(f"📅 Уведомление: {notification_time.strftime('%d.%m.%Y %H:%M')} UTC")
            print(f"🎈 Событие: {event['event_start'].strftime('%d.%m.%Y %H:%M')} UTC")
            return event
    
    print(f"❌ Не найдено событий для уведомления (допуск ±{tolerance.total_seconds():.0f} секунд)")
    
    # Показываем ближайшие уведомления для отладки
    next_event = get_next_notification_event()
    if next_event:
        nt = next_event['notification_time']
        et = next_event['event_start']
        time_until = (nt - now).total_seconds()
        print(f"📅 Следующее уведомление: {nt.strftime('%d.%m.%Y %H:%M')} UTC")
        print(f"🎈 Следующее событие: {et.strftime('%d.%m.%Y %H:%M')} UTC")
        print(f"⏰ До уведомления: {time_until/3600:.1f} часов")
    
    return None

def get_next_notification_event():
    """Получает следующее событие для планирования"""
    now = datetime.now(pytz.UTC)
    events = calculate_next_events(now, count=10)
    
    for event in events:
        if event['notification_time'] > now:
            return event
    
    return None

def format_notification_message(event):
    """Форматирует сообщение для уведомления в момент появления острова"""
    # Получаем время события
    event_start = event['event_start']
    event_end = event['event_end']
    
    # Конвертируем в киевское время (UTC+2/+3)
    kiev_tz = pytz.timezone('Europe/Kiev')
    event_start_kiev = event_start.astimezone(kiev_tz)
    event_end_kiev = event_end.astimezone(kiev_tz)
    
    # Получаем следующее событие
    now = datetime.now(pytz.UTC)
    next_events = calculate_next_events(now, count=5)
    
    next_event = None
    for next_ev in next_events:
        if next_ev['event_start'] > event['event_start']:
            next_event = next_ev
            break
    
    # Новый формат уведомления
    message = f"ЕБУЧИЙ ШАР прибыл!\n"
    
    # Добавляем время следующего события если есть
    if next_event:
        next_kiev = next_event['event_start'].astimezone(kiev_tz)
        message += f"Следующие прибытие: {next_kiev.strftime('%H:%M')}"
    else:
        # Если не удалось определить следующее событие, показываем стандартное время
        next_time = event_start + EVENT_INTERVAL
        next_kiev = next_time.astimezone(kiev_tz)
        message += f"Следующие прибытие: {next_kiev.strftime('%H:%M')}"
    
    return message

def schedule_next_notification():
    """Планирует следующее уведомление (сначала FastCron, потом cron-job.org)"""
    next_event = get_next_notification_event()
    if not next_event:
        print("❌ Не найдено следующее событие для планирования")
        return False
    
    notification_time = next_event['notification_time']
    event_start = next_event['event_start']
    
    print(f"📅 Планируем следующее уведомление:")
    print(f"   Уведомление: {notification_time.strftime('%d.%m.%Y %H:%M')} UTC")
    print(f"   Событие: {event_start.strftime('%d.%m.%Y %H:%M')} UTC")
    print(f"   В момент появления острова")
    
    # Сначала пробуем FastCron (лучше с rate limiting)
    try:
        from setup_fastcron import create_single_notification_job as create_fastcron_job
        fastcron_api_key = os.environ.get('FASTCRON_API_KEY')
        if fastcron_api_key:
            print(f"🚀 Пробуем FastCron API...")
            result = create_fastcron_job(notification_time)
            if result:
                print(f"✅ FastCron: следующее уведомление запланировано")
                return result
            else:
                print(f"⚠️ FastCron не сработал, пробуем cron-job.org...")
        else:
            print(f"📝 FASTCRON_API_KEY не настроен, пробуем cron-job.org...")
    except ImportError:
        print(f"📝 Модуль setup_fastcron недоступен, пробуем cron-job.org...")
    
    # Откат на cron-job.org
    try:
        from setup_cronjob import create_single_notification_job as create_cronjob_job
        return create_cronjob_job(notification_time)
    except ImportError as e:
        print(f"⚠️ Модули планирования недоступны: {e}")
        return False

def show_schedule_info():
    """Показывает информацию о расписании событий"""
    now = datetime.now(pytz.UTC)
    events = calculate_next_events(now, count=5)
    
    print(f"📅 РАСПИСАНИЕ FLOATING ISLAND")
    print("=" * 50)
    print(f"⏰ Текущее время: {now.strftime('%d.%m.%Y %H:%M')} UTC")
    print(f"🔄 Интервал: {EVENT_INTERVAL.total_seconds()/3600:.1f} часов")
    print(f"⏳ Уведомления: в момент события")
    print(f"🎈 Продолжительность: {EVENT_DURATION.seconds//60} минут")
    print()
    
    kiev_tz = pytz.timezone('Europe/Kiev')
    
    for i, event in enumerate(events, 1):
        notification_time = event['notification_time']
        event_start = event['event_start']
        
        nt_kiev = notification_time.astimezone(kiev_tz)
        et_kiev = event_start.astimezone(kiev_tz)
        
        time_until_notification = (notification_time - now).total_seconds()
        time_until_event = (event_start - now).total_seconds()
        
        print(f"🎈 Событие {i}:")
        print(f"   📢 Уведомление: {nt_kiev.strftime('%d.%m %H:%M')} (Киев)")
        print(f"   🎈 Событие: {et_kiev.strftime('%d.%m %H:%M')} (Киев)")
        
        if time_until_notification > 0:
            hours = int(time_until_notification // 3600)
            print(f"   ⏰ До уведомления: {hours} ч.")
        elif time_until_event > 0:
            hours = int(time_until_event // 3600)
            print(f"   ⏰ До события: {hours} ч.")
        else:
            print(f"   ✅ Событие прошло")
        print()

def main():
    """Основная функция - отправляет уведомление и планирует следующее"""
    print(f"🤖 Запуск проверки Floating Island Bot...")
    print(f"⏰ Текущее время: {datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    # Проверяем аргументы командной строки для тестовых режимов
    if len(sys.argv) > 1:
        if sys.argv[1] == '--test' or sys.argv[1] == '--test-send':
            test_notification()
            return
        elif sys.argv[1] == '--schedule':
            show_schedule_info()
            return
    
    # Проверяем, есть ли событие для уведомления прямо сейчас
    current_event = get_current_notification_event()
    
    if current_event:
        print(f"🚨 Остров ПОЯВИЛСЯ! Отправляем уведомление:")
        notification_time = current_event['notification_time']
        event_start = current_event['event_start']
        
        print(f"   Время уведомления: {notification_time.strftime('%H:%M')} UTC")
        print(f"   Остров появился: {event_start.strftime('%H:%M')} UTC")
        
        message = format_notification_message(current_event)
        
        if send_telegram_message(message):
            print(f"✅ Уведомление отправлено успешно")
            
            # Планируем следующее уведомление
            print(f"\n🔄 Планируем следующее уведомление...")
            if schedule_next_notification():
                print(f"✅ Следующее уведомление запланировано")
            else:
                print(f"⚠️ Не удалось запланировать следующее уведомление")
        else:
            print(f"❌ Ошибка отправки уведомления")
    else:
        print("📭 Нет событий для уведомления в данный момент")
        print("💡 Возможно, бот запущен не в точное время уведомления")
        
        # Показываем ближайшие события для справки
        next_event = get_next_notification_event()
        if next_event:
            nt = next_event['notification_time']
            et = next_event['event_start']
            print(f"📅 Следующее уведомление: {nt.strftime('%d.%m.%Y %H:%M')} UTC")
            print(f"🎈 Следующее событие: {et.strftime('%d.%m.%Y %H:%M')} UTC")

def test_notification():
    """Отправляет тестовое уведомление для проверки работы бота"""
    print("🧑‍🔬 ТЕСТ СИСТЕМЫ УВЕДОМЛЕНИЙ")
    print("=" * 50)
    
    now = datetime.now(pytz.UTC)
    print(f"⏰ Время теста: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    # Проверяем настройки
    if not BOT_TOKEN:
        print("❌ Ошибка: TELEGRAM_BOT_TOKEN не установлен")
        return False
    
    if not CHAT_ID:
        print("❌ Ошибка: TELEGRAM_CHAT_ID не установлен")
        return False
    
    print(f"🤖 Токен бота: {BOT_TOKEN[:10]}...{BOT_TOKEN[-4:]}")
    print(f"💬 Chat ID: {CHAT_ID}")
    print()
    
    # Показываем информацию о ближайших событиях
    next_event = get_next_notification_event()
    if next_event:
        nt = next_event['notification_time']
        et = next_event['event_start']
        kiev_tz = pytz.timezone('Europe/Kiev')
        et_kiev = et.astimezone(kiev_tz)
        
        print(f"📅 Ближайшее событие:")
        print(f"   Уведомление: {nt.strftime('%d.%m.%Y %H:%M')} UTC")
        print(f"   Событие: {et_kiev.strftime('%d.%m.%Y %H:%M')} (Киев)")
        print()
    
    # Создаем тестовое сообщение
    test_message = f"""🧑‍🔬 <b>ТЕСТ СИСТЕМЫ УВЕДОМЛЕНИЙ</b>

✅ Бот Floating Island работает!

📅 <b>Время теста:</b> {now.strftime('%d.%m.%Y %H:%M:%S')} UTC
📶 <b>Статус:</b> Подключение к Telegram работает
🎈 <b>Готовность:</b> Система готова к отправке уведомлений

⏰ <b>Параметры системы:</b>
• Уведомления в момент появления острова
• Интервал между событиями: {EVENT_INTERVAL.total_seconds()/3600:.1f} часов
• Продолжительность события: {EVENT_DURATION.seconds//60} минут

🔔 Если вы видите это сообщение, значит бот настроен правильно!"""

    # Отправляем тестовое сообщение
    if send_telegram_message(test_message):
        print("✅ Тестовое сообщение отправлено успешно!")
        print("🎉 Система работает корректно!")
        return True
    else:
        print("❌ Ошибка отправки тестового сообщения")
        return False

if __name__ == "__main__":
    main()