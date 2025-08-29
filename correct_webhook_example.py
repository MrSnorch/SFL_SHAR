#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def show_correct_webhook_format():
    """Показывает правильный формат webhook URL для разных случаев"""
    
    print("✅ ПРАВИЛЬНЫЙ ФОРМАТ WEBHOOK URL")
    print("=" * 50)
    
    print("\n📌 Общий формат:")
    print("https://api.github.com/repos/{owner}/{repo}/dispatches")
    
    print("\n📝 Примеры:")
    
    print("\n1. Для публичного репозитория:")
    print("   https://api.github.com/repos/MrSnorch/SFL_SHAR/dispatches")
    
    print("\n2. Для приватного репозитория (тот же формат):")
    print("   https://api.github.com/repos/MrSnorch/SFL_SHAR/dispatches")
    
    print("\n3. Для форка:")
    print("   https://api.github.com/repos/ваш_логин/SFL_SHAR/dispatches")
    
    print("\n⚠️ НЕПРАВИЛЬНЫЕ ФОРМАТЫ:")
    print("❌ https://github.com/MrSnorch/SFL_SHAR/dispatches")
    print("❌ https://api.github.com/MrSnorch/SFL_SHAR/dispatches")
    print("❌ https://api.github.com/repos/MrSnorch/SFL_SHAR")
    print("❌ https://api.github.com/repos/MrSnorch/SFL_SHAR/actions")
    
    print("\n📋 Как проверить правильность:")
    print("1. Убедитесь, что URL начинается с: https://api.github.com/repos/")
    print("2. За этим следует: {владелец}/{название_репозитория}")
    print("3. Заканчивается на: /dispatches")
    
    print("\n🔧 Пример для вашего случая:")
    print("Если ваш репозиторий: https://github.com/MrSnorch/SFL_SHAR")
    print("То WEBHOOK_URL должен быть:")
    print("https://api.github.com/repos/MrSnorch/SFL_SHAR/dispatches")

if __name__ == "__main__":
    show_correct_webhook_format()