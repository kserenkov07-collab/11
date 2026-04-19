# interface.py
# ПОЛНЫЙ ИНТЕРФЕЙС ТОРГОВОЙ СИСТЕМЫ
# Автор: Колин для выживания деревни

import asyncio
import pandas as pd
from datetime import datetime, timedelta
from config import TICKERS, TRADE_SETTINGS

class TradingInterface:
    def __init__(self, trading_system, data_manager):
        self.trading_system = trading_system
        self.data_manager = data_manager
        self.current_view = "main"
        self.selected_ticker = None
        
    async def display_main_screen(self):
        """Отображение главного экрана"""
        print("\n" + "=" * 80)
        print("SURVIVAL TRADING SYSTEM - ГЛАВНЫЙ ЭКРАН")
        print("=" * 80)
        print(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Статус: Анализ рынка каждую минуту")
        print(f"Токен: {'✓' if self.trading_system.client else '✗'}")
        print("\nДоступные разделы:")
        print("1. Текущие сигналы")
        print("2. История сигналов")
        print("3. Портфель")
        print("4. Графики анализа")
        print("5. Настройки")
        print("6. Выход")
        print("=" * 80)
        
        choice = input("Выберите раздел (1-6): ")
        return choice
        
    async def display_signals(self, signals):
        """Отображение текущих сигналов"""
        print("\n" + "=" * 80)
        print("ТЕКУЩИЕ ТОРГОВЫЕ СИГНАЛЫ")
        print("=" * 80)
        
        if not signals:
            print("Нет активных сигналов")
            return
            
        for i, signal in enumerate(signals):
            action_color = "\033[92m" if signal['action'] == 'BUY' else "\033[91m"
            reset_color = "\033[0m"
            
            print(f"{i+1}. {action_color}{signal['ticker']}: {signal['action']}{reset_color}")
            print(f"   Текущая цена: {signal['current_price']:.2f} ₽")
            print(f"   Целевая цена: {signal['target_price']:.2f} ₽")
            print(f"   Прогнозируемый рост: {signal['predicted_growth']:.2f}%")
            print(f"   Рекомендуется держать до: {signal['exit_date']}")
            print(f"   Уверенность: {signal['confidence']}")
            print(f"   Время сигнала: {signal['timestamp'].strftime('%H:%M:%S')}")
            print("-" * 40)
        
        print("\nДействия:")
        print("1. Исполнить все сигналы")
        print("2. Выбрать сигнал для исполнения")
        print("3. Вернуться в главное меню")
        
        choice = input("Выберите действие (1-3): ")
        return choice
        
    async def display_history(self):
        """Отображение истории сигналов"""
        print("\n" + "=" * 80)
        print("ИСТОРИЯ ТОРГОВЫХ СИГНАЛОВ")
        print("=" * 80)
        
        if not self.trading_system.signals_history:
            print("История сигналов пуста")
            return
            
        for i, signal in enumerate(self.trading_system.signals_history[-20:]):  # Последние 20 сигналов
            action_color = "\033[92m" if signal['action'] == 'BUY' else "\033[91m"
            reset_color = "\033[0m"
            
            print(f"{i+1}. {action_color}{signal['ticker']}: {signal['action']}{reset_color}")
            print(f"   Время: {signal['timestamp'].strftime('%Y-%m-%d %H:%M')}")
            print(f"   Цена входа: {signal['current_price']:.2f} ₽")
            print(f"   Прогноз роста: {signal['predicted_growth']:.2f}%")
            print(f"   Рекомендация: Держать до {signal['exit_date']}")
            print("-" * 40)
            
        input("\nНажмите Enter для возврата...")
        
    async def display_portfolio(self):
        """Отображение портфеля"""
        print("\n" + "=" * 80)
        print("СОСТОЯНИЕ ПОРТФЕЛЯ")
        print("=" * 80)
        
        if not self.trading_system.portfolio:
            print("Портфель пуст")
            return
            
        total_value = 0
        for ticker, position in self.trading_system.portfolio.items():
            value = position['quantity'] * position['current_price']
            total_value += value
            pnl = (position['current_price'] - position['entry_price']) * position['quantity']
            pnl_percent = (position['current_price'] / position['entry_price'] - 1) * 100
            
            print(f"{ticker}:")
            print(f"  Количество: {position['quantity']}")
            print(f"  Цена входа: {position['entry_price']:.2f} ₽")
            print(f"  Текущая цена: {position['current_price']:.2f} ₽")
            print(f"  P&L: {pnl:.2f} ₽ ({pnl_percent:.2f}%)")
            print(f"  Стоимость: {value:.2f} ₽")
            print("-" * 30)
            
        print(f"Общая стоимость портфеля: {total_value:.2f} ₽")
        input("\nНажмите Enter для возврата...")
        
    async def display_analysis_charts(self):
        """Отображение графиков анализа"""
        print("\n" + "=" * 80)
        print("ГРАФИКИ АНАЛИТИКИ")
        print("=" * 80)
        
        print("Доступные графики:")
        print("1. График цены и скользящих средних")
        print("2. RSI индикатор")
        print("3. MACD индикатор")
        print("4. Боллинжер Бэнды")
        print("5. Прогноз цены на 6 месяцев")
        print("6. Вернуться в главное меню")
        
        choice = input("Выберите график (1-6): ")
        
        if choice in ['1', '2', '3', '4', '5']:
            ticker = input("Введите тикер (например, SBER): ").upper()
            if ticker in self.trading_system.tickers:
                self.selected_ticker = ticker
                await self.generate_chart(choice, ticker)
            else:
                print("Неверный тикер")
                input("Нажмите Enter для продолжения...")
                
        return choice
        
    async def generate_chart(self, chart_type, ticker):
        """Генерация выбранного графика"""
        print(f"\nГенерация графика для {ticker}...")
        
        # Здесь будет код для генерации реальных графиков
        # В реальной системе это бы использовало matplotlib или plotly
        
        if chart_type == '1':
            print(f"[ГРАФИК] Цена и скользящие средние для {ticker}")
            print("┌─────────────────────────────────────────────────────────────┐")
            print("│                    Цена и MA(20), MA(50), MA(200)           │")
            print("│                                                             │")
            print("│    Цена ──────                                              │")
            print("│    MA(20) ────                                              │")
            print("│    MA(50) ────                                              │")
            print("│    MA(200) ───                                              │")
            print("│                                                             │")
            print("└─────────────────────────────────────────────────────────────┘")
            
        elif chart_type == '2':
            print(f"[ГРАФИК] RSI индикатор для {ticker}")
            print("┌─────────────────────────────────────────────────────────────┐")
            print("│                         RSI(14)                             │")
            print("│                                                             │")
            print("│    Перекупленность (70+) ────────────────────────────       │")
            print("│                                                             │")
            print("│    Нейтральная зона ────────────────────────────────        │")
            print("│                                                             │")
            print("│    Перепроданность (30-) ──────────────────────────         │")
            print("└─────────────────────────────────────────────────────────────┘")
            
        elif chart_type == '3':
            print(f"[ГРАФИК] MACD индикатор для {ticker}")
            print("┌─────────────────────────────────────────────────────────────┐")
            print("│                         MACD                                │")
            print("│                                                             │")
            print("│    MACD линия ──────────────                                │")
            print("│    Сигнальная линия ───────                                 │")
            print("│    Гистограмма ────────────                                 │")
            print("│                                                             │")
            print("└─────────────────────────────────────────────────────────────┘")
            
        elif chart_type == '4':
            print(f"[ГРАФИК] Боллинжер Бэнды для {ticker}")
            print("┌─────────────────────────────────────────────────────────────┐")
            print("│                    Боллинжер Бэнды                          │")
            print("│                                                             │")
            print("│    Верхняя полоса ──────────────────────────────             │")
            print("│    Средняя полоса (MA20) ──────────────────────              │")
            print("│    Нижняя полоса ─────────────────────────────               │")
            print("│    Цена ──────────────────────────────────────               │")
            print("└─────────────────────────────────────────────────────────────┘")
            
        elif chart_type == '5':
            print(f"[ГРАФИК] Прогноз цены на 6 месяцев для {ticker}")
            print("┌─────────────────────────────────────────────────────────────┐")
            print("│                    6-месячный прогноз                       │")
            print("│                                                             │")
            print("│    Исторические данные ────────────                          │")
            print("│    Прогноз ──────────────────────                            │")
            print("│    Доверительный интервал ────────                           │")
            print("│                                                             │")
            print("└─────────────────────────────────────────────────────────────┘")
            
        input("\nНажмите Enter для возврата...")
        
    async def display_settings(self):
        """Отображение настроек"""
        print("\n" + "=" * 80)
        print("НАСТРОЙКИ СИСТЕМЫ")
        print("=" * 80)
        
        print("Текущие настройки:")
        print(f"1. Интервал анализа: {self.trading_system.trade_settings['analysis_interval']} сек")
        print(f"2. Количество для торговли: {self.trading_system.trade_settings['trade_quantity']}")
        print(f"3. Уровень риска: {self.trading_system.trade_settings['risk_level']}")
        print("4. Изменить настройки")
        print("5. Вернуться в главное меню")
        
        choice = input("Выберите действие (1-5): ")
        
        if choice == '4':
            new_interval = input("Новый интервал анализа (сек): ")
            new_quantity = input("Новое количество для торговли: ")
            new_risk = input("Новый уровень риска (LOW/MEDIUM/HIGH): ")
            
            if new_interval:
                self.trading_system.trade_settings['analysis_interval'] = int(new_interval)
            if new_quantity:
                self.trading_system.trade_settings['trade_quantity'] = int(new_quantity)
            if new_risk:
                self.trading_system.trade_settings['risk_level'] = new_risk.upper()
                
            print("Настройки обновлены!")
            input("Нажмите Enter для продолжения...")
            
        return choice
        
    async def execute_all_signals(self, signals):
        """Исполнение всех сигналов"""
        print("\nИсполнение всех сигналов...")
        
        for signal in signals:
            if signal['confidence'] == 'HIGH':
                quantity = self.trading_system.trade_settings['trade_quantity']
                await self.trading_system.execute_trade(
                    self.trading_system.tickers[signal['ticker']], 
                    signal['action'], 
                    quantity
                )
                
                # Обновление портфеля
                if signal['ticker'] not in self.trading_system.portfolio:
                    self.trading_system.portfolio[signal['ticker']] = {
                        'quantity': quantity,
                        'entry_price': signal['current_price'],
                        'current_price': signal['current_price'],
                        'entry_time': datetime.now()
                    }
                else:
                    if signal['action'] == 'BUY':
                        self.trading_system.portfolio[signal['ticker']]['quantity'] += quantity
                    else:  # SELL или SHORT
                        self.trading_system.portfolio[signal['ticker']]['quantity'] -= quantity
        
        print("Все сигналы исполнены!")
        input("Нажмите Enter для продолжения...")
        
    async def run(self):
        """Запуск интерфейса"""
        print("Запуск интерфейса торговой системы...")
        
        # Инициализация торговой системы
        if not await self.trading_system.initialize():
            print("Ошибка инициализации торговой системы!")
            return
            
        # Основной цикл интерфейса
        while True:
            if self.current_view == "main":
                choice = await self.display_main_screen()
                
                if choice == '1':
                    # Показать текущие сигналы
                    _, signals = await self.trading_system.analyze_market()
                    signal_choice = await self.display_signals(signals)
                    
                    if signal_choice == '1':
                        await self.execute_all_signals(signals)
                    elif signal_choice == '2':
                        selected = input("Выберите номер сигнала: ")
                        # Реализация выбора конкретного сигнала
                        print("Функция в разработке...")
                        input("Нажмите Enter для продолжения...")
                        
                elif choice == '2':
                    await self.display_history()
                elif choice == '3':
                    await self.display_portfolio()
                elif choice == '4':
                    await self.display_analysis_charts()
                elif choice == '5':
                    await self.display_settings()
                elif choice == '6':
                    print("Выход из системы...")
                    break
                else:
                    print("Неверный выбор!")
                    input("Нажмите Enter для продолжения...")
