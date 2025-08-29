#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json
from datetime import datetime, timedelta
import pytz

# Настройки для теста
FASTCRON_API_KEY = os.environ.get('FASTCRON_API_KEY', 'your-fastcron-api-key')
FASTCRON_BASE_URL = 'https://app.fastcron.com/api'

# Тестовые параметры
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', 'https://api.github.com/repos/test/test/actions/workflows/12345/dispatches')
GITHUB_TOKEN = os.environ.get('GH_TOKEN', 'ghp_test-token')

def test_fastcron_post_request():
    """Тест POST запроса к FastCron API"""
    print("🔍 ТЕСТИРОВАНИЕ POST ЗАПРОСА К FASTCRON API")
    print("=" * 50)
    
    # Вычисляем время через 1 минуту для теста
    test_time = datetime.now(pytz.UTC) + timedelta(minutes=1)
    
    # Создаем cron выражение
    cron_expression = f"{test_time.minute} {test_time.hour} {test_time.day} {test_time.month} *"
    
    print(f"⏰ Время теста: {test_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"⚙️ Cron выражение: {cron_expression}")
    print()
    
    # Подготавливаем postData для GitHub webhook
    post_data = json.dumps({
        "event_type": "test_event",
        "client_payload": {
            "test_time": test_time.isoformat(),
            "test": True
        },
        "ref": "main"  # Обязательный параметр для GitHub Actions
    })
    
    # HTTP заголовки
    http_headers = f"Authorization: token {GITHUB_TOKEN}\\r\\nAccept: application/vnd.github.v3+json\\r\\nContent-Type: application/json"
    
    # Параметры для FastCron API
    payload = {
        'token': FASTCRON_API_KEY,
        'name': f'Test Job {test_time.strftime("%H:%M")}',
        'expression': cron_expression,
        'url': WEBHOOK_URL,
        'httpMethod': 'POST',
        'postData': post_data,
        'httpHeaders': http_headers,
        'timezone': 'UTC',
        'notify': 'false'
    }
    
    print("📤 Отправляем POST запрос к FastCron API...")
    print(f"🔗 URL: {FASTCRON_BASE_URL}/v1/cron_add")
    print()
    
    try:
        # Выполняем POST запрос
        response = requests.post(
            f"{FASTCRON_BASE_URL}/v1/cron_add",
            json=payload,
            timeout=30
        )
        
        print(f"📥 Статус ответа: {response.status_code}")
        print(f"📥 Заголовки ответа: {dict(response.headers)}")
        
        # Пытаемся получить JSON ответ
        try:
            result = response.json()
            print(f"📥 Тело ответа (JSON):")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            if response.status_code == 200 and result.get('status') == 'success':
                print("✅ Запрос выполнен успешно!")
                job_id = result.get('data', {}).get('id')
                if job_id:
                    print(f"🆔 ID созданного задания: {job_id}")
                    # Пытаемся удалить тестовое задание
                    delete_test_job(job_id)
                return True
            else:
                print("❌ Запрос не удался")
                print(f"📝 Сообщение: {result.get('message', 'Нет сообщения')}")
                return False
                
        except json.JSONDecodeError:
            print("📥 Тело ответа (текст):")
            print(response.text)
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сети: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def delete_test_job(job_id):
    """Удаляем тестовое задание после создания"""
    print(f"\n🗑️ Удаляем тестовое задание {job_id}...")
    
    try:
        response = requests.post(
            f"{FASTCRON_BASE_URL}/v1/cron_delete",
            json={
                'token': FASTCRON_API_KEY,
                'id': job_id
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                print("✅ Тестовое задание удалено успешно")
            else:
                print(f"❌ Ошибка удаления: {result.get('message', 'Неизвестная ошибка')}")
        else:
            print(f"❌ Ошибка HTTP при удалении: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка при удалении задания: {e}")

def test_fastcron_list():
    """Тест получения списка заданий"""
    print("\n📋 ТЕСТИРОВАНИЕ ПОЛУЧЕНИЯ СПИСКА ЗАДАНИЙ")
    print("=" * 50)
    
    try:
        response = requests.post(
            f"{FASTCRON_BASE_URL}/v1/cron_list",
            json={'token': FASTCRON_API_KEY},
            timeout=30
        )
        
        print(f"📥 Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                print("✅ Получение списка заданий успешно")
                crons = result.get('data', [])
                print(f"📊 Найдено заданий: {len(crons)}")
                for i, cron in enumerate(crons[:3]):  # Показываем первые 3 задания
                    print(f"  {i+1}. {cron.get('name', 'Без названия')} (ID: {cron.get('id')})")
                if len(crons) > 3:
                    print(f"  ... и еще {len(crons) - 3} заданий")
                return True
            else:
                print(f"❌ Ошибка: {result.get('message', 'Неизвестная ошибка')}")
                return False
        else:
            print(f"❌ Ошибка HTTP: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при получении списка: {e}")
        return False

if __name__ == "__main__":
    print("🚀 ТЕСТ FASTCRON API")
    print("=" * 50)
    
    # Проверяем наличие API ключа
    if FASTCRON_API_KEY == 'your-fastcron-api-key':
        print("⚠️  Не установлен FASTCRON_API_KEY")
        print("💡 Установите переменную окружения или измените значение в скрипте")
        exit(1)
    
    print(f"🔑 API ключ: {FASTCRON_API_KEY[:10]}...{FASTCRON_API_KEY[-4:]}")
    print(f"🔗 Базовый URL: {FASTCRON_BASE_URL}")
    print()
    
    # Выполняем тесты
    success1 = test_fastcron_post_request()
    success2 = test_fastcron_list()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("🎉 Все тесты пройдены успешно!")
        print("✅ FastCron API работает корректно")
    else:
        print("❌ Некоторые тесты не пройдены")
        print("💡 Проверьте API ключ и настройки подключения")