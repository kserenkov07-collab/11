"""
Главный модуль приложения.
Точка входа с оптимизацией запуска и обработки ошибок.
"""
import ctypes
import platform
import tkinter as tk
import sys
import os
import traceback
from config import Config  # Импортируем Config в начале

def hide_console():
    """Скрытие консольного окна (только для Windows)"""
    if platform.system() == "Windows":
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

def main():
    """Основная функция с обработкой ошибков и оптимизацией"""
    # Скрываем консоль после запуска GUI
    hide_console()
    
    try:
        # Загрузка настроек
        Config.load_settings()
        
        # Проверка и подготовка окружения
        from installer import check_environment
        if not check_environment():
            print("Ошибка подготовки окружения!")
            sys.exit(1)
        
        # Проверка словарей BIP-39
        if not os.path.exists(Config.WORDLISTS_DIR) or not os.listdir(Config.WORDLISTS_DIR):
            print("Словари BIP-39 не найдены!")
            response = input("Загрузить словари? (y/n): ")
            if response.lower() == 'y':
                from installer import download_bip39_wordlists
                if not download_bip39_wordlists():
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
                print(f"Загружен словарь {lang}: {len(wordlists[lang])} слов")
            else:
                print(f"Словарь {lang} не найден!")
                sys.exit(1)
        
        # Проверяем, что словари содержат достаточно слов
        for lang, words in wordlists.items():
            if len(words) < 2048:
                print(f"Словарь {lang} содержит недостаточно слов: {len(words)} вместо 2048")
                sys.exit(1)
        
        # Импорты после проверки окружения
        from quantum_gui import QuantumWalletGUI
        from async_manager import async_manager
        
        # Запуск GUI
        root = tk.Tk()
        app = QuantumWalletGUI(root)
        
        # Обработка закрытия окна
        def on_closing():
            if app.is_running:
                if tk.messagebox.askokcancel("Выход", "Проверка仍在运行。确定要退出吗?"):
                    app.stop_checking()
                    # Останавливаем менеджер асинхронных операций
                    async_manager.stop()
                    root.destroy()
            else:
                # Останавливаем менеджер асинхронных операций
                async_manager.stop()
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()
        
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        traceback.print_exc()
        input("Нажмите Enter для выхода...")
        sys.exit(1)

if __name__ == "__main__":
    main()
