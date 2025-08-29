#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import pytz

def demo_notification_format():
    """Демонстрирует новый формат уведомлений"""
    
    # Текущее время для примера
    now_utc = datetime(2025, 8, 29, 23, 34, 0)
    kiev_tz = pytz.timezone('Europe/Kiev')
    now_kyiv = now_utc.astimezone(kiev_tz)
    
    # Новый упрощенный формат
    message = f"""🎈 ЕБУЧИЙ ШАР прибыл!

Киев: {now_kyiv.strftime('%H:%M')}
UTC: {now_utc.strftime('%H:%M')}"""
    
    print("НОВЫЙ ФОРМАТ УВЕДОМЛЕНИЙ:")
    print("=" * 30)
    print(message)
    print("=" * 30)
    
    # Старый формат для сравнения
    end_time = now_kyiv + timedelta(minutes=30)
    next_time = now_kyiv + timedelta(hours=8, minutes=20)
    
    old_message = f"""🎈 <b>ЕБУЧИЙ ШАР прибыл!</b>

⏰ <b>Доступен сейчас:</b>
   🇺🇦 Киев: {now_kyiv.strftime('%H:%M')} ({now_kyiv.strftime('%d.%m')})
   🌍 UTC: {now_utc.strftime('%H:%M')} ({now_utc.strftime('%d.%m')})

⏳ <b>Продолжительность:</b> 30 минут
   (до {end_time.strftime('%H:%M')} по Киеву)

Следующее прибытие в {next_time.strftime('%H:%M')}"""
    
    print("\nСТАРЫЙ ФОРМАТ УВЕДОМЛЕНИЙ:")
    print("=" * 30)
    print(old_message)
    print("=" * 30)

if __name__ == "__main__":
    demo_notification_format()