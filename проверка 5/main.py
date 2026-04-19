"""
Главный модуль приложения.
Точка входа с оптимизацией запуска и обработки ошибок.
"""
import tkinter as tk
import sys
import os
import traceback
from config import Config
from logger import logger, setup_logger  # Импортируем setup_logger

def main():
    """Основная функция с обработкой ошибков и оптимизацией"""
    try:
        # Перенастраиваем логгер для GUI перед инициализацией
        Config.LOG_TO_CONSOLE = False  # Отключаем вывод в консоль
        
        logger.info("Запуск приложения Wallet Scanner")
        
        # Загрузка настроек
        Config.load_settings()
        logger.info("Настройки загружены")
        
        # Проверка и подготовка окружения
        from installer import check_environment
        if not check_environment():
            logger.error("Ошибка подготовки окружения!")
            print("Ошибка подготовки окружения!")
            sys.exit(1)
        
        # Проверка словарей BIP-39
        if not os.path.exists(Config.WORDLISTS_DIR) or not os.listdir(Config.WORDLISTS_DIR):
            logger.error("Словари BIP-39 не найдены!")
            print("Словари BIP-39 не найдены!")
            response = input("Загрузить словари? (y/n): ")
            if response.lower() == 'y':
                from installer import download_bip39_wordlists
                if not download_bip39_wordlists():
                    logger.error("Не удалось загрузить словари!")
                    print("Не удалось загрузить словари!")
                    sys.exit(1)
            else:
                sys.exit(1)
        
        # Дополнительная проверка: есть ли слова в словарях
        wordlists = {}
        for lang in Config.ENABLED_LANGUAGES:
            wordlist_file = os.path.join(Config.WORDLISTS_DIR, f"{lang}.txt")
            if os.path.exists(wordlist_file):
                with open(wordlist_file, 'r', encoding='utf-8') as f:
                    wordlists[lang] = [line.strip() for line in f.readlines()]
                logger.info(f"Загружен словарь {lang}: {len(wordlists[lang])} слов")
            else:
                logger.error(f"Словарь {lang} не найден!")
                print(f"Словарь {lang} не найден!")
                sys.exit(1)
        
        # Проверяем, что словари содержат достаточно слов
        for lang, words in wordlists.items():
            if len(words) < 2048:
                logger.error(f"Словарь {lang} содержит недостаточно слов: {len(words)} вместо 2048")
                print(f"Словарь {lang} содержит недостаточно слов: {len(words)} вместо 2048")
                sys.exit(1)
        
        # Импорты после проверки окружения
        from quantum_gui import QuantumWalletGUI
        from async_manager import async_manager
        
        # Запуск GUI
        root = tk.Tk()
        app = QuantumWalletGUI(root)
        logger.info("GUI инициализирован")
        
        # Обработка закрытия окна
        def on_closing():
            if app.is_running:
                if tk.messagebox.askokcancel("Выход", "Проверка?"):
                    logger.info("Остановка проверки и выход из приложения")
                    app.stop_checking()
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

if __name__ == "__main__":
    main()
