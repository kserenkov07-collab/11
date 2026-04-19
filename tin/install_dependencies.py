# install_dependencies.py
# СКРИПТ ДЛЯ УСТАНОВКИ ВСЕХ НЕОБХОДИМЫХ БИБЛИОТЕК
# Автор: Колин для выживания деревни

import subprocess
import sys
import os

def install_package(package):
    """Установка пакета с обработкой ошибок"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✓ Успешно установлен: {package}")
        return True
    except subprocess.CalledProcessError:
        print(f"✗ Ошибка установки: {package}")
        return False
    except Exception as e:
        print(f"✗ Неизвестная ошибка при установке {package}: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("УСТАНОВЩИК БИБЛИОТЕК ДЛЯ ТОРГОВОЙ СИСТЕМЫ")
    print("=" * 60)
    
    # Список всех необходимых библиотек
    required_packages = [
        "pandas",
        "numpy", 
        "scipy",
        "sympy",
        "matplotlib",
        "tinkoff-investments",
        "aiohttp",
        "scikit-learn",
        "selenium",
        "opcua",
        "pymodbus",
        "sqlalchemy",
        "beautifulsoup4",
        "requests",
        "textblob",
        "websockets",
        "lxml"
    ]
    
    print("Установка необходимых библиотек...")
    print("Это может занять несколько минут.")
    print("")
    
    # Установка библиотек
    success_count = 0
    for package in required_packages:
        if install_package(package):
            success_count += 1
    
    print("")
    print("=" * 60)
    print("РЕЗУЛЬТАТ УСТАНОВКИ:")
    print(f"Успешно установлено: {success_count} из {len(required_packages)}")
    
    if success_count == len(required_packages):
        print("✓ Все библиотеки успешно установлены!")
        print("Теперь вы можете запустить торговую систему.")
    else:
        print("⚠ Некоторые библиотеки не были установлены.")
        print("Пожалуйста, проверьте подключение к интернету и попробуйте снова.")
    
    print("")
    input("Нажмите Enter для выхода...")

if __name__ == "__main__":
    main()
