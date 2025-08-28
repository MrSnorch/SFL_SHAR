#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
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
NOTIFICATION_ADVANCE = timedelta(minutes=0)  # Уведомление В МОМЕНТ события
EVENT_DURATION = timedelta(minutes=30)  # Продолжительность события

def send_telegram_message(message: str):
    """Отправляет сообщение в Telegram"""
    if not BOT_TOKEN or not CHAT_ID:
        print(f"⚠️ Не настроены переменные окружения для Telegram")
        print(f"Сообщение: {message}")
        return False
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"✅ Уведомление отправлено успешно")
            return True
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
        notification_time = event_start - NOTIFICATION_ADVANCE  # = event_start (так как NOTIFICATION_ADVANCE = 0)
        
        events.append({
            'notification_time': notification_time,
            'event_start': event_start,
            'event_end': event_end,
            'event_number': i + 1
        })
        
        current_event += EVENT_INTERVAL
    
    return events

def get_current_notification_event():
    """Получает событие, которое начинается сейчас (в пределах ±2 минут)"""
    now = datetime.now(pytz.UTC)
    tolerance = timedelta(minutes=2)  # Допуск ±2 минуты
    
    print(f"🔍 Проверяем время появления острова: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    # Получаем события на ближайшие дни
    events = calculate_next_events(now - timedelta(days=1), count=100)
    
    for event in events:
        notification_time = event['notification_time']
        time_diff = abs((now - notification_time).total_seconds())
        
        if time_diff <= tolerance.total_seconds():
            print(f"✅ Найдено событие для уведомления: разница {time_diff:.0f} секунд")
            return event
    
    print(f"❌ Не найдено событий для уведомления (допуск ±{tolerance.total_seconds():.0f} секунд)")
    return None

def get_next_notification_event():
    """Получает следующее событие для планирования"""
    now = datetime.now(pytz.UTC)
    events = calculate_next_events(now, count=5)
    
    for event in events:
        if event['notification_time'] > now:
            return event
    
    return None

def format_notification_message(event):
    """Форматирует сообщение для уведомления"""
    # Получаем время следующего события
    now = datetime.now(pytz.UTC)
    next_events = calculate_next_events(now, count=2)
    
    # Ищем следующее событие после текущего
    next_event = None
    for next_ev in next_events:
        if next_ev['event_start'] > event['event_start']:
            next_event = next_ev
            break
    
    message = "ЕБУЧИЙ ШАР прибыл!"
    
    # Добавляем время следующего прибытия
    if next_event:
        next_time = next_event['event_start'].strftime('%H:%M')
        message += f"\n\nСледующее прибытие в {next_time}"
    
    return message

def schedule_next_notification():
    """Планирует следующее уведомление в cron-job.org"""
    next_event = get_next_notification_event()
    if not next_event:
        print("❌ Не найдено следующее событие для планирования")
        return False
    
    notification_time = next_event['notification_time']
    event_start = next_event['event_start']
    
    print(f"📅 Планируем следующее уведомление:")
    print(f"   Уведомление: {notification_time.strftime('%d.%m.%Y %H:%M')} UTC")
    print(f"   Событие: {event_start.strftime('%d.%m.%Y %H:%M')} UTC")
    
    # Импортируем функцию создания задания
    try:
        from setup_cronjob import create_single_notification_job
        return create_single_notification_job(notification_time)
    except ImportError:
        print("⚠️ Модуль setup_cronjob недоступен для автопланирования")
        return False

def main():
    """Основная функция - отправляет уведомление и планирует следующее"""
    print(f"🤖 Запуск точной проверки Floating Island...")
    print(f"⏰ Текущее время: {datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    # Проверяем, есть ли событие для уведомления прямо сейчас
    current_event = get_current_notification_event()
    
    if current_event:
        print(f"🚨 Остров ПОЯВИЛСЯ! Отправляем уведомление:")
        notification_time = current_event['notification_time']
        event_start = current_event['event_start']
        
        print(f"   Время уведомления: {notification_time.strftime('%H:%M')} UTC")
        print(f"   Остров доступен: {event_start.strftime('%H:%M')} UTC")
        
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
            print(f"📅 Следующее уведомление: {nt.strftime('%d.%m.%Y %H:%M')} UTC")

def test_notification():
    """Отправляет тестовое уведомление для проверки работы бота"""
    print("🧑‍🔬 ТЕСТ ОТПРАВКИ УВЕДОМЛЕНИЙ")
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
    
    # Создаем тестовое сообщение
    test_message = f"""🧑‍🔬 <b>ТЕСТ СИСТЕМЫ</b>

✅ Бот Floating Island работает!

📅 <b>Время теста:</b> {now.strftime('%d.%m.%Y %H:%M:%S')} UTC
📶 <b>Статус:</b> Подключение к Telegram работает
🏝️ <b>Готовность:</b> Система готова к отправке уведомлений

⏰ Ближайшее уведомление: <code>29.08.2025 01:00 UTC</code>

🚀 Система автоматических уведомлений запущена!"""
    
    print("\n📤 Отправляем тестовое сообщение:")
    print("-" * 50)
    print(test_message)
    print("-" * 50)
    
    # Отправляем сообщение
    success = send_telegram_message(test_message)
    
    if success:
        print("✅ ТЕСТ ПРОШЕЛ УСПЕШНО!")
        print("📡 Бот может отправлять сообщения в вашу группу")
        print("🏝️ Система уведомлений Floating Island готова к работе!")
        return True
    else:
        print("❌ ТЕСТ НЕ ПРОШЕЛ!")
        print("🔧 Проверьте:")
        print("   - Правильность TELEGRAM_BOT_TOKEN")
        print("   - Правильность TELEGRAM_CHAT_ID")
        print("   - Добавлен ли бот в группу")
        print("   - Есть ли у бота права на отправку сообщений")
        return False

def test_mode():
    """Тестовый режим - показывает ближайшие события без отправки"""
    print("🧪 ТЕСТОВЫЙ РЕЖИМ")
    print("=" * 50)
    
    now = datetime.now(pytz.UTC)
    print(f"⏰ Текущее время: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    # Показываем ближайшие 5 событий
    events = calculate_next_events(now, count=5)
    
    print(f"\n📅 Ближайшие 5 событий Floating Island:")
    print("-" * 50)
    
    for i, event in enumerate(events, 1):
        notification_time = event['notification_time']
        event_start = event['event_start']
        event_end = event['event_end']
        
        print(f"{i}. Остров появляется: {notification_time.strftime('%d.%m %H:%M')} UTC")
        print(f"   Доступен:         {event_start.strftime('%d.%m %H:%M')} - {event_end.strftime('%H:%M')} UTC")
        print()
    
    # Проверяем текущее событие
    print("-" * 50)
    current_event = get_current_notification_event()
    if current_event:
        print("🔔 ТЕКУЩЕЕ СОБЫТИЕ ДЛЯ УВЕДОМЛЕНИЯ:")
        message = format_notification_message(current_event)
        print(f"Сообщение:\n{message}\n")
        print("📤 В реальном режиме это сообщение было бы отправлено в Telegram")
    else:
        print("📭 Нет событий для уведомления в текущее время")
        
        # Показываем следующее событие
        next_event = get_next_notification_event()
        if next_event:
            nt = next_event['notification_time']
            et = next_event['event_start']
            time_until = nt - now
            hours = int(time_until.total_seconds() // 3600)
            minutes = int((time_until.total_seconds() % 3600) // 60)
            
            print(f"📅 Следующее уведомление: {nt.strftime('%d.%m.%Y %H:%M')} UTC")
            print(f"🏝️ Событие: {et.strftime('%d.%m.%Y %H:%M')} UTC")
            print(f"⏳ Осталось: {hours} час {minutes} минут")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--test':
            test_mode()
        elif sys.argv[1] == '--test-send':
            test_notification()
        else:
            print("❌ Неизвестная команда")
            print("Доступные опции:")
            print("  --test      - показать расписание без отправки")
            print("  --test-send - отправить тестовое сообщение")
    else:
        main()
