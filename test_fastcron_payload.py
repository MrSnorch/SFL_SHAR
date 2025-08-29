#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import requests

def test_fastcron_payload_format():
    """Тест правильного формата payload для FastCron API"""
    print("ПРАВИЛЬНЫЙ ФОРМАТ PAYLOAD ДЛЯ FASTCRON API:")
    
    # Пример payload для создания задания в FastCron
    payload = {
        'token': 'your-api-token-here',
        'name': 'Test Job',
        'expression': '0 0 * * *',  # Ежедневно в 00:00
        'url': 'https://api.github.com/repos/owner/repo/actions/workflows/12345/dispatches',
        'httpMethod': 'POST',
        'postData': json.dumps({
            "event_type": "test_event",
            "client_payload": {
                "message": "test"
            },
            "ref": "main"
        }),
        'httpHeaders': 'Authorization: token ghp_your_token\\r\\nAccept: application/vnd.github.v3+json\\r\\nContent-Type: application/json',
        'timezone': 'UTC',
        'notify': 'false'
    }
    
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print()
    
    # Показываем, как должен выглядеть POST запрос
    print("ПРИМЕР POST ЗАПРОСА:")
    print("POST https://app.fastcron.com/api/v1/cron_add")
    print("Content-Type: application/json")
    print()
    print("Тело запроса:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    print("Тест формата POST запроса к FastCron API")
    print("=" * 50)
    test_fastcron_payload_format()
    print()
    print("Важно: FastCron API ожидает POST запрос с JSON телом, включая 'ref': 'main' в postData")