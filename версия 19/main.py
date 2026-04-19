"""
Точка входа приложения.
"""
import tkinter as tk
import sys
import os
import traceback
from config import config
from logger import logger, setup_logger

def main():
    """Основная функция с обработкой ошибок и оптимизацией"""
    try:
        # Перенастраиваем логгер для GUI перед инициализацией
        config.LOG_TO_CONSOLE = True  # Убедимся, что вывод в консоль включен
        
        logger.info("Запуск приложения Wallet Scanner")
        
        # Загрузка настроек
        config.load_settings()
        logger.info("Настройки загружены")
        
        # Проверка и подготовка окружения
        if not check_environment():
            logger.error("Ошибка подготовки окружения!")
            print("Ошибка подготовки окружения!")
            print("Пожалуйста, установите необходимые зависимости:")
            print("pip install requests ecdsa base58 pycryptodome Pillow aiohttp")
            input("Нажмите Enter для выхода...")
            sys.exit(1)
        
        # Проверка словарей BIP-39
        if not os.path.exists(config.WORDLISTS_DIR) or not os.listdir(config.WORDLISTS_DIR):
            logger.error("Словари BIP-39 не найдены!")
            print("Словари BIP-39 не найдены!")
            response = input("Загрузить словари? (y/n): ")
            if response.lower() == 'y':
                if not download_bip39_wordlists():
                    logger.error("Не удалось загрузить словари!")
                    print("Не удалось загрузить словари!")
                    sys.exit(1)
            else:
                sys.exit(1)
        
        # Дополнительная проверка: есть ли слова в словарях
        wordlists = {}
        for lang in config.ENABLED_LANGUAGES:
            wordlist_file = os.path.join(config.WORDLISTS_DIR, f"{lang}.txt")
            if os.path.exists(wordlist_file):
                with open(wordlist_file, 'r', encoding='utf-8') as f:
                    wordlists[lang] = [line.strip() for line in f.readlines()]
                logger.info(f"Загружен словарь {lang}: {len(wordlists[lang])} слов")
            else:
                logger.error(f"Словарь {lang} не найден!")
                print(f"Словарь {lang} не найден!")

        # Если нет ни одного словаря, выходим
        if not wordlists:
            logger.error("Не загружено ни одного словаря BIP-39!")
            print("Не загружено ни одного словаря BIP-39!")
            sys.exit(1)

        # Проверяем, что словари содержат достаточно слов
        for lang, words in wordlists.items():
            if len(words) < 2048:
                logger.error(f"Словарь {lang} содержит недостаточно слов: {len(words)} вместо 2048")
                print(f"Словарь {lang} содержит недостаточно слов: {len(words)} вместо 2048")

        # Обновляем список доступных языков
        config.ENABLED_LANGUAGES = list(wordlists.keys())
        
        # Импорты после проверки окружения
        from app import Application
        from async_manager import async_manager
        
        # Запуск GUI
        root = tk.Tk()
        app = Application()
        logger.info("Приложение инициализировано")
        
        # Обработка закрытия окна
        def on_closing():
            if app.is_running:
                import tkinter.messagebox as messagebox
                if messagebox.askokcancel("Выход", "Проверка активна. Вы уверены, что хотите выйти?"):
                    logger.info("Остановка проверки и выход из приложения")
                    app.stop()
                    # Останавливаем менеджер асинхронных операций
                    async_manager.stop()
                    root.destroy()
            else:
                # Останавливаем менеджер асинхронных операций
                async_manager.stop()
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        logger.info("Запуск основного цикла приложения")
        root.mainloop()
        
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")
        logger.critical(traceback.format_exc())
        print(f"Критическая ошибка: {e}")
        traceback.print_exc()
        input("Нажмите Enter для выхода...")
        sys.exit(1)

def check_environment():
    """Проверка окружения"""
    try:
        # Проверяем необходимые модули
        import requests
        import ecdsa
        import base58
        import aiohttp
        from Crypto.Hash import keccak, RIPEMD160, SHA256
        
        logger.info("Все необходимые модули доступны")
        return True
    except ImportError as e:
        logger.error(f"Отсутствует необходимый модуль: {e}")
        return False

def download_bip39_wordlists():
    """Загрузка словарей BIP-39"""
    import requests
    
    bip39_files = {
        "english.txt": "https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/english.txt",
        "french.txt": "https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/french.txt",
        "spanish.txt": "https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/spanish.txt",
        "italian.txt": "https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/italian.txt",
        "portuguese.txt": "https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/portuguese.txt",
    }
    
    success_count = 0
    for filename, url in bip39_files.items():
        try:
            file_path = os.path.join(config.WORDLISTS_DIR, filename)
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            logger.info(f"Загружен словарь: {filename}")
            success_count += 1
        except Exception as e:
            logger.error(f"Ошибка загрузки словаря {filename}: {e}")
    
    return success_count > 0

if __name__ == "__main__":
    main()