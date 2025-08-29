#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from datetime import datetime
import pytz

def test_correct_format():
    """Тест правильного формата для GitHub workflow dispatch"""
    print("ПРАВИЛЬНЫЙ ФОРМАТ (СООТВЕТСТВУЕТ WORKFLOW ФАЙЛУ):")
    correct_payload = {
        'ref': 'main',
        'inputs': {
            'action': 'test'  # Единственный разрешенный параметр из workflow файла
        }
    }
    print(json.dumps(correct_payload, indent=2, ensure_ascii=False))
    print()

def test_incorrect_format():
    """Тест неправильного формата с лишними параметрами"""
    print("НЕПРАВИЛЬНЫЙ ФОРМАТ (ЛИШНИЕ ПАРАМЕТРЫ):")
    incorrect_payload = {
        'ref': 'main',
        'inputs': {
            'action': 'test',
            'test': 'true',        # Не разрешен в workflow файле
            'timestamp': datetime.now(pytz.UTC).isoformat()  # Не разрешен в workflow файле
        }
    }
    print(json.dumps(incorrect_payload, indent=2, ensure_ascii=False))
    print()

if __name__ == "__main__":
    print("Тест форматов GitHub Workflow Dispatch Payload")
    print("=" * 50)
    test_incorrect_format()
    test_correct_format()
    print("GitHub workflow принимает только параметры, объявленные в workflow_dispatch.inputs")
    print("В нашем случае это только 'action' и 'count'")