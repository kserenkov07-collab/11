# graphics.py
# МОДУЛЬ ДЛЯ ГЕНЕРАЦИИ ГРАФИКОВ
# Автор: Колин для выживания деревни

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import io
import base64

class ChartGenerator:
    def __init__(self):
        plt.style.use('dark_background')
        
    def generate_price_chart(self, historical_data, predictions=None):
        """Генерация графика цены и скользящих средних"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Исторические данные
        ax.plot(historical_data['date'], historical_data['close'], label='Цена', linewidth=2)
        
        # Скользящие средние
        if 'MA_20' in historical_data.columns:
            ax.plot(historical_data['date'], historical_data['MA_20'], label='MA(20)', alpha=0.7)
        if 'MA_50' in historical_data.columns:
            ax.plot(historical_data['date'], historical_data['MA_50'], label='MA(50)', alpha=0.7)
        if 'MA_200' in historical_data.columns:
            ax.plot(historical_data['date'], historical_data['MA_200'], label='MA(200)', alpha=0.7)
            
        # Прогнозы если есть
        if predictions is not None:
            last_date = historical_data['date'].iloc[-1]
            future_dates = [last_date + timedelta(days=i) for i in range(1, len(predictions)+1)]
            ax.plot(future_dates, predictions, label='Прогноз', linestyle='--', color='orange')
            
        ax.set_title('График цены и скользящих средних')
        ax.set_xlabel('Дата')
        ax.set_ylabel('Цена (₽)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Сохранение в байты
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        
        return img_str
        
    def generate_rsi_chart(self, historical_data):
        """Генерация графика RSI"""
        if 'RSI' not in historical_data.columns:
            return None
            
        fig, ax = plt.subplots(figsize=(12, 4))
        
        ax.plot(historical_data['date'], historical_data['RSI'], label='RSI', linewidth=2)
        ax.axhline(70, color='red', linestyle='--', alpha=0.7, label='Перекупленность')
        ax.axhline(30, color='green', linestyle='--', alpha=0.7, label='Перепроданность')
        ax.axhline(50, color='gray', linestyle='--', alpha=0.5)
        
        ax.set_title('Индекс относительной силы (RSI)')
        ax.set_xlabel('Дата')
        ax.set_ylabel('RSI')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 100)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        
        return img_str
        
    def generate_macd_chart(self, historical_data):
        """Генерация графика MACD"""
        if 'MACD' not in historical_data.columns or 'MACD_Signal' not in historical_data.columns:
            return None
            
        fig, ax = plt.subplots(figsize=(12, 4))
        
        ax.plot(historical_data['date'], historical_data['MACD'], label='MACD', linewidth=2)
        ax.plot(historical_data['date'], historical_data['MACD_Signal'], label='Сигнальная линия', linewidth=2)
        
        # Гистограмма MACD
        histogram = historical_data['MACD'] - historical_data['MACD_Signal']
        ax.bar(historical_data['date'], histogram, label='Гистограмма', alpha=0.3)
        
        ax.set_title('MACD индикатор')
        ax.set_xlabel('Дата')
        ax.set_ylabel('MACD')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.axhline(0, color='gray', linestyle='-', alpha=0.5)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        
        return img_str
        
    def generate_bollinger_bands(self, historical_data):
        """Генерация графика Боллинжер Бэндов"""
        if 'BB_Upper' not in historical_data.columns or 'BB_Lower' not in historical_data.columns:
            return None
            
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.plot(historical_data['date'], historical_data['close'], label='Цена', linewidth=2)
        ax.plot(historical_data['date'], historical_data['BB_Upper'], label='Верхняя полоса', alpha=0.7)
        ax.plot(historical_data['date'], historical_data['BB_Middle'], label='Средняя полоса (MA20)', alpha=0.7)
        ax.plot(historical_data['date'], historical_data['BB_Lower'], label='Нижняя полоса', alpha=0.7)
        
        # Заполнение между полосами
        ax.fill_between(historical_data['date'], historical_data['BB_Upper'], historical_data['BB_Lower'], alpha=0.1)
        
        ax.set_title('Боллинжер Бэнды')
        ax.set_xlabel('Дата')
        ax.set_ylabel('Цена (₽)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        
        return img_str
        
    def generate_forecast_chart(self, historical_data, predictions):
        """Генерация графика прогноза"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Исторические данные
        ax.plot(historical_data['date'], historical_data['close'], label='Исторические данные', linewidth=2)
        
        # Прогноз
        last_date = historical_data['date'].iloc[-1]
        future_dates = [last_date + timedelta(days=i) for i in range(1, len(predictions)+1)]
        ax.plot(future_dates, predictions, label='Прогноз', linewidth=2, color='orange')
        
        # Область доверительного интервала
        std = np.std(historical_data['close'].pct_change()) * predictions
        upper_band = predictions + std
        lower_band = predictions - std
        
        ax.fill_between(future_dates, lower_band, upper_band, alpha=0.2, color='orange', label='Доверительный интервал')
        
        ax.set_title('6-месячный прогноз цены')
        ax.set_xlabel('Дата')
        ax.set_ylabel('Цена (₽)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        
        return img_str
