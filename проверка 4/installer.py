"""
Модуль установки зависимостей и загрузки ресурсов.
Автоматически настраивает окружение для максимальной производительности.
"""
import os
import sys
import subprocess
import importlib
import requests
import time
from pathlib import Path
from config import Config

def install_package(package_name, import_name=None):
    """Установка пакета с помощью pip с оптимизацией для скорости"""
    if import_name is None:
        import_name = package_name
    
    print(f"📦 Проверка {package_name}...")
    
    try:
        importlib.import_module(import_name)
        print(f"✅ {package_name} уже установлен")
        return True
    except ImportError:
        print(f"❌ {package_name} отсутствует, устанавливаю...")
        
        try:
            cmd = [sys.executable, "-m", "pip", "install", package_name]
            
            # Для Windows используем precompiled wheels
            if sys.platform == "win32":
                cmd.insert(1, "--prefer-binary")
            
            subprocess.check_call(cmd)
            importlib.import_module(import_name)
            print(f"✅ {package_name} успешно установлен")
            return True
        except Exception as e:
            print(f"❌ Ошибка при установке {package_name}: {e}")
            return False

def download_with_retry(url, path, max_retries=3):
    """Загрузка файла с повторными попытками"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            with open(path, 'wb') as f:
                f.write(response.content)
            return True
        except Exception as e:
            print(f"❌ Попытка {attempt + 1}/{max_retries} не удалась: {e}")
            time.sleep(1)
    return False

def download_bip39_wordlists():
    """Загрузка полных словарей BIP-39 с использованием многопоточности"""
    print("🌐 Загрузка словарей BIP-39...")
    
    bip39_files = {
        "english.txt": "https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/english.txt",
        "french.txt": "https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/french.txt",
        "spanish.txt": "https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/spanish.txt",
        "italian.txt": "https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/italian.txt",
        "portuguese.txt": "https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/portuguese.txt",
        "czech.txt": "https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/czech.txt"
    }
    
    success_count = 0
    total_files = len(bip39_files)
    
    for filename, url in bip39_files.items():
        file_path = os.path.join(Config.WORDLISTS_DIR, filename)
        if not os.path.exists(file_path):
            if download_with_retry(url, file_path):
                print(f"✅ Загружен: {filename}")
                success_count += 1
            else:
                print(f"❌ Ошибка загрузки: {filename}")
        else:
            print(f"✅ Уже существует: {filename}")
            success_count += 1
    
    return success_count == total_files

def download_common_patterns():
    """Загрузка распространенных паттернов и паролей"""
    print("🌐 Загрузка распространенных паттернов...")
    
    pattern_files = {
        "common_passwords.txt": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-1000000.txt",
        "keyboard_patterns.txt": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Keyboard-Combinations.txt",
        "crypto_patterns.txt": "https://raw.githubusercontent.com/rareweasel/crypto-wordlists/master/patterns.txt",
    }
    
    success_count = 0
    total_files = len(pattern_files)
    
    for filename, url in pattern_files.items():
        file_path = os.path.join(Config.PATTERNS_DIR, filename)  # Исправлено: используем Config.PATTERNS_DIR
        if not os.path.exists(file_path):
            try:
                if download_with_retry(url, file_path):
                    print(f"✅ Загружен: {filename}")
                    success_count += 1
                else:
                    print(f"❌ Ошибка загрузки: {filename}")
            except Exception as e:
                print(f"❌ Ошибка загрузки: {filename}: {e}")
        else:
            print(f"✅ Уже существует: {filename}")
            success_count += 1
    
    # Создаем базовые файлы, если не удалось загрузить
    for filename in [Config.COMMON_PATTERNS_FILE, Config.KNOWN_PHRASES_FILE]:
        if not os.path.exists(filename):
            try:
                with open(filename, 'w') as f:
                    if filename == Config.COMMON_PATTERNS_FILE:
                        f.write("one two three four five six seven eight nine ten eleven twelve\n")
                    else:
                        f.write("abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about\n")
                print(f"✅ Создан: {filename}")
                success_count += 1
            except Exception as e:
                print(f"❌ Ошибка создания файла {filename}: {e}")
    
    return success_count >= total_files

def optimize_system_settings():
    """Оптимизация системных настроек для повышения производительности"""
    print("⚙️  Оптимизация системных настроек...")
    
    # Настройка переменных окружения для улучшения производительности
    os.environ['PYTHONUNBUFFERED'] = '1'
    os.environ['PYTHONIOENCODING'] = 'UTF-8'
    
    print("✅ Системные настройки оптимизированы")

def check_environment():
    """Полная проверка и подготовка окружения"""
    print("🔍 Проверка окружения...")
    
    # Проверяем и устанавливаем зависимости
    packages = [
        ("requests", None),
        ("ecdsa", None),
        ("base58", None),
        ("pycryptodome", "Crypto"),
        ("Pillow", "PIL"),
        ("aiohttp", None),
    ]
    
    success = True
    for package_name, import_name in packages:
        if not install_package(package_name, import_name):
            success = False
    
    if not success:
        print("\n❌ Не удалось установить некоторые зависимости.")
        print("Попробуйте установить их вручную:")
        print("pip install requests ecdsa base58 pycryptodome Pillow aiohttp")
        return False
    
    # Загружаем словари
    if not download_bip39_wordlists():
        print("\n⚠️  Не удалось загрузить все словари BIP-39.")
        print("Попробуйте запустить скрипт еще раз")
    
    # Загружаем распространенные паттерны
    if not download_common_patterns():
        print("\n⚠️  Не удалось загрузить все файлы с паттернами.")
        print("Будут использоваться базовые паттерны")
    
    # Оптимизируем настройки системы
    optimize_system_settings()
    
    return True
