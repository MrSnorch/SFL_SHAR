#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import pytz

def demo_new_notification_format():
    """Демонстрирует новый формат уведомлений"""
    
    # Текущее время для примера
    now_utc = datetime(2025, 8, 29, 9, 20, 0)
    kiev_tz = pytz.timezone('Europe/Kiev')
    now_kyiv = now_utc.astimezone(kiev_tz)
    
    # Следующее событие через 8 часов 20 минут
    next_event = now_utc + timedelta(hours=8, minutes=20)
    next_kyiv = next_event.astimezone(kiev_tz)
    
    # Новый формат уведомления
    new_message = f"""ЕБУЧИЙ ШАР прибыл!
Следующие прибытие: {next_kyiv.strftime('%H:%M')}"""
    
    print("НОВЫЙ ФОРМАТ УВЕДОМЛЕНИЙ:")
    print("=" * 30)
    print(new_message)
    print("=" * 30)
    
    # Старый формат для сравнения
    old_message = f"""🎈 ЕБУЧИЙ ШАР прибыл!

Киев: {now_kyiv.strftime('%H:%M')}
UTC: {now_utc.strftime('%H:%M')}"""
    
    print("\nСТАРЫЙ ФОРМАТ УВЕДОМЛЕНИЙ:")
    print("=" * 30)
    print(old_message)
    print("=" * 30)

if __name__ == "__main__":
    demo_new_notification_format()