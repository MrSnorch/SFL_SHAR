#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from datetime import datetime
import pytz

def test_old_format():
    """Test the old (incorrect) format"""
    print("OLD FORMAT (INCORRECT):")
    old_payload = {
        'event_type': 'floating_island_notification',
        'client_payload': {
            'notification_time': datetime.now(pytz.UTC).isoformat(),
            'auto_scheduled': True
        }
    }
    print(json.dumps(old_payload, indent=2, ensure_ascii=False))
    print()

def test_new_format():
    """Test the new (correct) format"""
    print("NEW FORMAT (CORRECT):")
    new_payload = {
        'ref': 'main',
        'inputs': {
            'action': 'notify',
            'notification_time': datetime.now(pytz.UTC).isoformat(),
            'auto_scheduled': 'true'
        }
    }
    print(json.dumps(new_payload, indent=2, ensure_ascii=False))
    print()

if __name__ == "__main__":
    print("Testing GitHub API payload formats")
    print("=" * 50)
    test_old_format()
    test_new_format()
    print("The new format should work with GitHub workflow dispatches")