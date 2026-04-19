# main.py
# УПРОЩЕННАЯ ВЕРСИЯ ГЛАВНОГО ФАЙЛА
# Автор: Колин для выживания деревни

import asyncio
import threading
from datetime import datetime
from dependencies import DependencyManager
from trading_system import AdvancedTradingSystem
from data_manager import DataManager
from interface import TradingInterface

# Проверяем доступность зависимостей
deps = DependencyManager()
missing_deps = deps.get_missing_deps()

if missing_deps:
    print("⚠ Отсутствуют некоторые зависимости:")
    for dep in missing_deps:
        print(f"  - {dep}")
    print("Система будет работать в упрощенном режиме.")
    print("Для установки всех зависимостей запустите: pip install -r requirements.txt")
    print()

class SimplifiedTradingApplication:
    def __init__(self):
        self.trading_system = AdvancedTradingSystem("t.539HFY_GqB1uWwZh1ZU4KwloBrrmUWg9vG-1NvZw-R-LDZulElYZyZRHqXkLWIjkOndsbb8o__VO-BhXZmDjmg")
        self.data_manager = DataManager()
        self.interface = TradingInterface(self.trading_system, self.data_manager)
        self.stop_event = threading.Event()

    async def initialize_system(self):
        """Инициализация всех компонентов системы"""
        print("=" * 80)
        print("SURVIVAL TRADING SYSTEM - УПРОЩЕННАЯ ВЕРСИЯ")
        print("=" * 80)
        print("Инициализация системы...")
        
        # Инициализация торговой системы
        if not await self.trading_system.initialize():
            print("Ошибка инициализации торговой системы!")
            return False
            
        print("Система успешно инициализирована!")
        return True

    async def run(self):
        """Запуск приложения"""
        try:
            # Инициализация системы
            if not await self.initialize_system():
                return
                
            # Запуск основного интерфейса
            await self.interface.run()
            
        except Exception as e:
            print(f"Критическая ошибка: {e}")
        finally:
            # Корректное завершение работы
            self.stop_event.set()

async def main():
    # Создание и запуск приложения
    app = SimplifiedTradingApplication()
    await app.run()

if __name__ == "__main__":
    # Запуск асинхронного event loop
    asyncio.run(main())
