import yaml
import sys

try:
    with open('.github/workflows/floating-island.yml', 'r', encoding='utf-8') as f:
        yaml.safe_load(f)
    print('✅ YAML is valid')
except Exception as e:
    print(f'❌ YAML error: {e}')
    sys.exit(1)