#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json
from datetime import datetime
import pytz

def test_webhook():
    """Тестирует webhook для GitHub Actions"""
    print("🚀 ТЕСТ WEBHOOK")
    print("=" * 50)
    
    # Получаем переменные окружения
    webhook_url = os.environ.get('WEBHOOK_URL')
    github_token = os.environ.get('GITHUB_TOKEN')
    
    print(f"WEBHOOK_URL: {webhook_url}")
    print(f"GITHUB_TOKEN задан: {'✅' if github_token else '❌'}")
    print()
    
    # Проверяем URL
    if not webhook_url:
        print("❌ WEBHOOK_URL не задан")
        return False
    
    if not github_token:
        print("❌ GITHUB_TOKEN не задан")
        return False
    
    # Проверяем формат URL
    if not webhook_url.startswith('https://api.github.com/repos/'):
        print("❌ Неправильный формат URL. Должно начинаться с https://api.github.com/repos/")
        return False
    
    if not webhook_url.endswith('/dispatches'):
        print("❌ Неправильный формат URL. Должно заканчиваться на /dispatches")
        return False
    
    # Проверяем структуру
    try:
        parts = webhook_url.replace('https://api.github.com/repos/', '').replace('/dispatches', '').split('/')
        if len(parts) != 2 or not all(parts):
            print("❌ Неправильная структура URL")
            return False
        print(f"✅ Владелец: {parts[0]}")
        print(f"✅ Репозиторий: {parts[1]}")
    except Exception as e:
        print(f"❌ Ошибка проверки структуры URL: {e}")
        return False
    
    # Тестируем отправку
    print(f"\n📡 Отправляем тестовый webhook...")
    
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'event_type': 'test_webhook',
        'client_payload': {
            'timestamp': datetime.now(pytz.UTC).isoformat(),
            'test': True
        }
    }
    
    try:
        response = requests.post(webhook_url, headers=headers, json=payload, timeout=15)
        
        print(f"Статус ответа: {response.status_code}")
        
        if response.status_code == 204:
            print("✅ Webhook отправлен успешно!")
            print("GitHub Actions должен запуститься в течение нескольких секунд")
            return True
        elif response.status_code == 401:
            print("❌ Ошибка 401: Неверный токен")
            print("Проверьте GITHUB_TOKEN в GitHub Secrets")
            return False
        elif response.status_code == 403:
            print("❌ Ошибка 403: Нет прав доступа")
            print("Убедитесь, что токен имеет права 'repo' и 'workflow'")
            return False
        elif response.status_code == 404:
            print("❌ Ошибка 404: Репозиторий не найден")
            print("Проверьте правильность owner и repo в URL")
            return False
        else:
            print(f"❌ Неожиданный статус: {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Исключение при отправке: {e}")
        return False

def show_webhook_info():
    """Показывает информацию о webhook"""
    webhook_url = os.environ.get('WEBHOOK_URL')
    
    print("📋 ИНФОРМАЦИЯ О WEBHOOK")
    print("=" * 50)
    
    if webhook_url:
        print(f"Текущий URL: {webhook_url}")
        
        # Разбираем URL
        if webhook_url.startswith('https://api.github.com/repos/'):
            try:
                parts = webhook_url.replace('https://api.github.com/repos/', '').replace('/dispatches', '').split('/')
                if len(parts) == 2:
                    owner, repo = parts
                    print(f"Владелец: {owner}")
                    print(f"Репозиторий: {repo}")
                    print(f"GitHub: https://github.com/{owner}/{repo}")
            except:
                print("Не удалось разобрать URL")
    else:
        print("WEBHOOK_URL не задан")
    
    print(f"\n🔧 Правильный формат:")
    print(f"https://api.github.com/repos/{{owner}}/{{repo}}/dispatches")
    print(f"\n📝 Пример:")
    print(f"https://api.github.com/repos/MrSnorch/SFL_SHAR/dispatches")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'info':
        show_webhook_info()
    else:
        test_webhook()