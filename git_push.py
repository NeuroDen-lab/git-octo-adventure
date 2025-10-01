#!/usr/bin/env python3
"""
Скрипт для автоматического коммита и пуша в GitHub
Использование: python git_push.py [сообщение коммита]
"""

import subprocess
import sys
import os
from datetime import datetime

def run_command(command, description):
    """Выполняет команду и выводит результат"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            print(f"✅ {description} - успешно")
            if result.stdout.strip():
                print(f"   {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} - ошибка")
            if result.stderr.strip():
                print(f"   {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} - исключение: {e}")
        return False

def get_commit_message():
    """Получает сообщение коммита от пользователя или генерирует автоматическое"""
    if len(sys.argv) > 1:
        return sys.argv[1]
    
    # Автоматическое сообщение на основе изменений
    try:
        result = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            changes = result.stdout.strip().split('\n')
            modified_files = [line.split()[-1] for line in changes if line.startswith('M')]
            new_files = [line.split()[-1] for line in changes if line.startswith('A')]
            
            if new_files:
                return f"Добавлены новые файлы: {', '.join(new_files[:3])}"
            elif modified_files:
                return f"Обновлены файлы: {', '.join(modified_files[:3])}"
        
        return f"Обновление от {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    except:
        return f"Обновление от {datetime.now().strftime('%d.%m.%Y %H:%M')}"

def main():
    print("🚀 Автоматический коммит и пуш в GitHub")
    print("=" * 50)
    
    # Проверяем, что мы в Git репозитории
    if not os.path.exists('.git'):
        print("❌ Ошибка: не найден Git репозиторий")
        return False
    
    # Получаем сообщение коммита
    commit_message = get_commit_message()
    print(f"📝 Сообщение коммита: {commit_message}")
    print()
    
    # Проверяем статус
    if not run_command("git status", "Проверка статуса"):
        return False
    
    # Добавляем все изменения
    if not run_command("git add .", "Добавление файлов"):
        return False
    
    # Проверяем, есть ли изменения для коммита
    result = subprocess.run("git diff --cached --quiet", shell=True, capture_output=True)
    if result.returncode == 0:
        print("ℹ️  Нет изменений для коммита")
        return True
    
    # Создаем коммит
    if not run_command(f'git commit -m "{commit_message}"', "Создание коммита"):
        return False
    
    # Получаем информацию о ветке
    result = subprocess.run("git branch --show-current", shell=True, capture_output=True, text=True)
    current_branch = result.stdout.strip() if result.returncode == 0 else "main"
    
    # Проверяем, настроен ли удаленный репозиторий
    result = subprocess.run("git remote -v", shell=True, capture_output=True, text=True)
    if not result.stdout.strip():
        print("⚠️  Удаленный репозиторий не настроен")
        print("   Для настройки выполните:")
        print("   git remote add origin <URL_вашего_репозитория>")
        return False
    
    # Пушим изменения
    if not run_command(f"git push origin {current_branch}", f"Отправка в GitHub (ветка {current_branch})"):
        return False
    
    print()
    print("🎉 Все операции выполнены успешно!")
    print(f"📊 Ветка: {current_branch}")
    print(f"💬 Коммит: {commit_message}")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
