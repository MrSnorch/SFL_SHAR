import os
import requests
import json

# Get environment variables
FASTCRON_API_KEY = os.environ.get('FASTCRON_API_KEY')

if not FASTCRON_API_KEY:
    print("❌ FASTCRON_API_KEY not set")
    exit(1)

print("🔍 Testing FastCron API connection...")

try:
    # Test the cron_list endpoint
    response = requests.post(
        'https://app.fastcron.com/api/v1/cron_list',
        json={'token': FASTCRON_API_KEY},
        timeout=10
    )
    
    print(f"📥 Status code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ FastCron API connection successful")
        print(f"📊 Found {len(result.get('data', []))} cron jobs")
    else:
        print(f"❌ FastCron API error: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"❌ Error connecting to FastCron API: {e}")