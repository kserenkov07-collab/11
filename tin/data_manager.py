# data_manager.py
# МЕНЕДЖЕР ДАННЫХ БЕЗ SQLALCHEMY (ВРЕМЕННАЯ ВЕРСИЯ)
# Автор: Колин для выживания деревни

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
import csv

class DataManager:
    def __init__(self):
        self.data_dir = "trading_data"
        
        # Создание директории для данных
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        # Загрузка истории и портфеля
        self.history = self.load_history()
        self.portfolio = self.load_portfolio()
        
    async def load_initial_data(self, trading_system):
        """Загрузка начальных данных"""
        print("Загрузка исторических данных...")
        
        # Загрузка данных для каждого тикера
        for ticker, figi in trading_system.tickers.items():
            try:
                data = await trading_system.get_historical_data(figi, years=2)
                if data is not None:
                    # Сохранение данных
                    file_path = os.path.join(self.data_dir, f"{ticker}_historical.csv")
                    data.to_csv(file_path, index=False)
                    print(f"Данные для {ticker} сохранены")
            except Exception as e:
                print(f"Ошибка загрузки данных для {ticker}: {e}")
                
    def load_history(self):
        """Загрузка истории торгов из файла"""
        history_file = os.path.join(self.data_dir, "trade_history.json")
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
        
    def load_portfolio(self):
        """Загрузка портфеля из файла"""
        portfolio_file = os.path.join(self.data_dir, "portfolio.json")
        if os.path.exists(portfolio_file):
            try:
                with open(portfolio_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
        
    def save_trade(self, trade_data):
        """Сохранение сделки в файл"""
        try:
            # Добавляем временную метку
            trade_data['timestamp'] = datetime.now().isoformat()
            
            # Добавляем в историю
            self.history.append(trade_data)
            
            # Сохраняем в файл
            history_file = os.path.join(self.data_dir, "trade_history.json")
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
                
            return True
        except Exception as e:
            print(f"Ошибка сохранения сделки: {e}")
            return False
            
    def save_industrial_data(self, industrial_data):
        """Сохранение промышленных данных в файл"""
        try:
            industrial_file = os.path.join(self.data_dir, "industrial_data.json")
            
            # Загрузка существующих данных
            if os.path.exists(industrial_file):
                with open(industrial_file, 'r', encoding='utf-8') as f:
                    all_data = json.load(f)
            else:
                all_data = []
                
            # Добавление новых данных
            for param, data in industrial_data.items():
                data['parameter'] = param
                data['timestamp'] = datetime.now().isoformat()
                all_data.append(data)
            
            # Сохранение
            with open(industrial_file, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)
                
            return True
        except Exception as e:
            print(f"Ошибка сохранения промышленных данных: {e}")
            return False
            
    def update_portfolio(self, ticker, quantity, price, action):
        """Обновление портфеля"""
        if ticker not in self.portfolio:
            self.portfolio[ticker] = {
                'quantity': 0,
                'entry_price': 0,
                'current_price': price,
                'total_invested': 0
            }
            
        if action == 'BUY':
            self.portfolio[ticker]['quantity'] += quantity
            self.portfolio[ticker]['total_invested'] += quantity * price
            self.portfolio[ticker]['entry_price'] = self.portfolio[ticker]['total_invested'] / self.portfolio[ticker]['quantity']
        else:  # SELL или SHORT
            self.portfolio[ticker]['quantity'] -= quantity
            self.portfolio[ticker]['total_invested'] -= quantity * self.portfolio[ticker]['entry_price']
            
        self.portfolio[ticker]['current_price'] = price
        
        # Если количество стало нулевым, удаляем тикер из портфеля
        if self.portfolio[ticker]['quantity'] <= 0:
            del self.portfolio[ticker]
            
        # Сохранение в файл
        self.save_portfolio()
        
    def save_portfolio(self):
        """Сохранение портфеля в файл"""
        try:
            portfolio_file = os.path.join(self.data_dir, "portfolio.json")
            with open(portfolio_file, 'w', encoding='utf-8') as f:
                json.dump(self.portfolio, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Ошибка сохранения портфеля: {e}")
            return False
            
    def get_portfolio_value(self, current_prices):
        """Расчет текущей стоимости портфеля"""
        total_value = 0
        for ticker, position in self.portfolio.items():
            if ticker in current_prices:
                position['current_price'] = current_prices[ticker]
                total_value += position['quantity'] * current_prices[ticker]
                
        self.save_portfolio()
        return total_value
        
    def get_performance_report(self):
        """Генерация отчета о производительности"""
        if not self.history:
            return "Нет данных для отчета"
            
        # Анализ прибыльности
        profitable_trades = [t for t in self.history if t.get('profit', 0) > 0]
        loss_trades = [t for t in self.history if t.get('profit', 0) < 0]
        
        total_profit = sum(t.get('profit', 0) for t in self.history)
        win_rate = len(profitable_trades) / len(self.history) * 100 if self.history else 0
        
        report = {
            'total_trades': len(self.history),
            'profitable_trades': len(profitable_trades),
            'loss_trades': len(loss_trades),
            'win_rate': win_rate,
            'total_profit': total_profit,
            'average_profit': total_profit / len(self.history) if self.history else 0
        }
        
        return report
        
    def save_news_data(self, news_data, sentiment):
        """Сохранение новостных данных"""
        try:
            news_file = os.path.join(self.data_dir, "news_data.json")
            news_records = {
                'timestamp': datetime.now().isoformat(),
                'news': news_data,
                'sentiment': sentiment
            }
            
            # Загрузка существующих данных
            if os.path.exists(news_file):
                with open(news_file, 'r', encoding='utf-8') as f:
                    all_news = json.load(f)
            else:
                all_news = []
                
            # Добавление новых данных
            all_news.append(news_records)
            
            # Сохранение
            with open(news_file, 'w', encoding='utf-8') as f:
                json.dump(all_news, f, ensure_ascii=False, indent=2)
                
            return True
        except Exception as e:
            print(f"Ошибка сохранения новостных данных: {e}")
            return False
            
    def save_economic_data(self, economic_data):
        """Сохранение экономических данных"""
        try:
            econ_file = os.path.join(self.data_dir, "economic_data.json")
            
            # Загрузка существующих данных
            if os.path.exists(econ_file):
                with open(econ_file, 'r', encoding='utf-8') as f:
                    all_econ_data = json.load(f)
            else:
                all_econ_data = {}
                
            # Добавление новых данных
            all_econ_data[datetime.now().isoformat()] = economic_data
            
            # Сохранение
            with open(econ_file, 'w', encoding='utf-8') as f:
                json.dump(all_econ_data, f, ensure_ascii=False, indent=2)
                
            return True
        except Exception as e:
            print(f"Ошибка сохранения экономических данных: {e}")
            return False
            
    def close(self):
        """Закрытие менеджера данных"""
        # Сохранение всех данных перед закрытием
        self.save_portfolio()
        
        history_file = os.path.join(self.data_dir, "trade_history.json")
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
