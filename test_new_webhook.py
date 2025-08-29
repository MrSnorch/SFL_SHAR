#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json
from datetime import datetime
import pytz

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

def test_new_webhook_format():
    """Тестирует новый формат webhook с правильным URL и payload"""
    print("🚀 ТЕСТ НОВОГО ФОРМАТА WEBHOOK")
    print("=" * 55)
    
    # Получаем переменные окружения
    webhook_url = os.environ.get('WEBHOOK_URL')
    github_token = os.environ.get('GITHUB_TOKEN')
    
    print(f"WEBHOOK_URL: {webhook_url}")
    print(f"GITHUB_TOKEN задан: {'✅' if github_token else '❌'}")
    print()
    
    # Проверяем обязательные переменные
    if not webhook_url:
        print("❌ WEBHOOK_URL не задан")
        return False
    
    if not github_token:
        print("❌ GITHUB_TOKEN не задан")
        return False
    
    # Формируем правильный URL для dispatches
    dispatch_url = get_github_dispatch_url(webhook_url)
    if not dispatch_url:
        print("❌ Не удалось сформировать правильный URL для dispatches")
        return False
    
    print(f"✅ Правильный dispatch URL: {dispatch_url}")
    
    # Подготавливаем заголовки
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }
    
    # Подготавливаем payload с обязательным "ref": "main"
    payload = {
        'event_type': 'test_webhook',
        'client_payload': {
            'timestamp': datetime.now(pytz.UTC).isoformat(),
            'test': True
        },
        'ref': 'main'  # Обязательное поле для нового формата
    }
    
    print(f"\n📡 Отправляем webhook с новым форматом...")
    print(f"📋 Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(dispatch_url, headers=headers, json=payload, timeout=15)
        
        print(f"\n📊 Результат запроса:")
        print(f"   Статус: {response.status_code}")
        
        if response.status_code == 204:
            print("✅ Webhook отправлен успешно!")
            print("🎉 GitHub Actions должен запуститься в течение нескольких секунд")
            return True
        elif response.status_code == 401:
            print("❌ Ошибка 401: Неверный токен")
            print("🔧 Проверьте GITHUB_TOKEN в GitHub Secrets")
            return False
        elif response.status_code == 403:
            print("❌ Ошибка 403: Нет прав доступа")
            print("🔧 Убедитесь, что токен имеет права 'repo' и 'workflow'")
            return False
        elif response.status_code == 404:
            print("❌ Ошибка 404: Workflow не найден")
            print("🔧 Проверьте правильность owner, repo и workflow ID")
            return False
        else:
            print(f"❌ Неожиданный статус: {response.status_code}")
            print(f"📄 Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Исключение при отправке: {e}")
        return False

def show_webhook_info():
    """Показывает информацию о webhook и правильный формат"""
    webhook_url = os.environ.get('WEBHOOK_URL')
    
    print("📋 ИНФОРМАЦИЯ О WEBHOOK")
    print("=" * 50)
    
    if webhook_url:
        print(f"Текущий WEBHOOK_URL: {webhook_url}")
        
        # Разбираем URL
        dispatch_url = get_github_dispatch_url(webhook_url)
        if dispatch_url:
            print(f"✅ Правильный dispatch URL: {dispatch_url}")
        else:
            print("❌ Не удалось сформировать dispatch URL")
    else:
        print("❌ WEBHOOK_URL не задан")
    
    print(f"\n🔧 Правильный формат URL для dispatches:")
    print(f"https://api.github.com/repos/{{owner}}/{{repo}}/actions/workflows/184853159/dispatches")
    
    print(f"\n📝 Пример:")
    print(f"https://api.github.com/repos/MrSnorch/SFL_SHAR/actions/workflows/184853159/dispatches")
    
    print(f"\n📦 Обязательный payload:")
    print(f"""{{
  "event_type": "test_webhook",
  "client_payload": {{
    "test": true,
    "timestamp": "{datetime.now(pytz.UTC).isoformat()}"
  }},
  "ref": "main"
}}""")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'info':
        show_webhook_info()
    else:
        test_new_webhook_format()