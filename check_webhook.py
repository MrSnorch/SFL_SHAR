#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json
from datetime import datetime
import pytz

def validate_webhook_url(url):
    """Проверяет правильность формата webhook URL"""
    if not url:
        return False, "URL не задан"
    
    if not url.startswith('https://api.github.com/repos/'):
        return False, "URL должен начинаться с https://api.github.com/repos/"
    
    if not '/dispatches' in url:
        return False, "URL должен заканчиваться на /dispatches"
    
    # Проверяем структуру URL
    parts = url.replace('https://api.github.com/repos/', '').replace('/dispatches', '').split('/')
    if len(parts) != 2:
        return False, "Неправильный формат. Должно быть: https://api.github.com/repos/{owner}/{repo}/dispatches"
    
    owner, repo = parts
    if not owner or not repo:
        return False, "Не указан владелец или репозиторий"
    
    return True, f"Правильный формат: владелец={owner}, репозиторий={repo}"

def test_webhook_url(url, token):
    """Тестирует webhook URL"""
    if not url or not token:
        return False, "Не задан URL или токен"
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }
    
    # Тестовый payload
    payload = {
        'event_type': 'test_webhook',
        'client_payload': {
            'test': True,
            'timestamp': datetime.now(pytz.UTC).isoformat()
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 204:
            return True, "Webhook работает корректно"
        elif response.status_code == 401:
            return False, "Неверный токен (401 Unauthorized)"
        elif response.status_code == 404:
            return False, "Репозиторий не найден (404 Not Found) - проверьте URL"
        elif response.status_code == 403:
            return False, "Нет прав доступа (403 Forbidden) - проверьте токен"
        else:
            return False, f"Ошибка {response.status_code}: {response.text}"
            
    except Exception as e:
        return False, f"Исключение: {e}"

def suggest_correct_url(current_url):
    """Предлагает правильный формат URL"""
    if not current_url:
        return "https://api.github.com/repos/{owner}/{repo}/dispatches"
    
    # Пытаемся извлечь owner и repo из текущего URL
    try:
        if 'github.com/' in current_url:
            parts = current_url.split('github.com/')
            if len(parts) > 1:
                path_parts = parts[1].split('/')
                if len(path_parts) >= 2:
                    owner, repo = path_parts[0], path_parts[1]
                    return f"https://api.github.com/repos/{owner}/{repo}/dispatches"
    except:
        pass
    
    return "https://api.github.com/repos/{owner}/{repo}/dispatches"

def main():
    """Основная функция проверки webhook"""
    print("🔍 ПРОВЕРКА WEBHOOK URL")
    print("=" * 50)
    
    # Получаем переменные окружения
    webhook_url = os.environ.get('WEBHOOK_URL')
    github_token = os.environ.get('GITHUB_TOKEN')
    
    print(f"Текущий WEBHOOK_URL: {webhook_url}")
    print(f"Токен задан: {'✅' if github_token else '❌'}")
    print()
    
    # Проверяем формат URL
    is_valid, message = validate_webhook_url(webhook_url)
    print(f"Формат URL: {'✅' if is_valid else '❌'} {message}")
    
    if not is_valid:
        correct_url = suggest_correct_url(webhook_url)
        print(f"\n💡 Предлагаемый правильный формат:")
        print(f"   {correct_url}")
    
    # Тестируем подключение если URL правильный
    if is_valid and github_token:
        print(f"\n📡 Тестирование подключения...")
        success, message = test_webhook_url(webhook_url, github_token)
        print(f"Результат: {'✅' if success else '❌'} {message}")
    
    print(f"\n📋 Инструкции по настройке:")
    print(f"1. WEBHOOK_URL должен быть в формате:")
    print(f"   https://api.github.com/repos/{{owner}}/{{repo}}/dispatches")
    print(f"2. Убедитесь, что GITHUB_TOKEN имеет права 'repo' и 'workflow'")
    print(f"3. Проверьте, что репозиторий существует")

if __name__ == "__main__":
    main()