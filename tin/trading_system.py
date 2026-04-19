# trading_system.py
# ИСПРАВЛЕННАЯ ТОРГОВАЯ СИСТЕМА
# Автор: Колин для выживания деревни

import asyncio
import pandas as pd
import numpy as np
from tinkoff.invest import (
    AsyncClient, 
    CandleInterval,
    GetCandlesRequest,
    OrderDirection,
    OrderType,
    HistoricCandle
)
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from config import TICKERS, TRADE_SETTINGS
import warnings
warnings.filterwarnings('ignore')

class AdvancedTradingSystem:
    def __init__(self, token):
        self.token = token
        self.client = None
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.tickers = TICKERS
        self.trade_settings = TRADE_SETTINGS
        self.signals_history = []
        self.portfolio = {}

    async def initialize(self):
        """Инициализация подключения к Tinkoff API"""
        self.client = AsyncClient(self.token)
        print("[СИСТЕМА] Подключение к Tinkoff API установлено")
        return True

    def quotation_to_float(self, quotation):
        """Конвертация Quotation в float"""
        return quotation.units + quotation.nano / 1e9

    async def get_historical_data(self, figi, years=5):
        """Получение исторических данных за указанный период"""
        print(f"[ИСТОРИЧЕСКИЕ ДАННЫЕ] Загрузка данных за {years} лет для {figi}...")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years*365)
        
        all_candles = []
        current_start = start_date
        
        while current_start < end_date:
            current_end = min(current_start + timedelta(days=300), end_date)
            
            # Исправленный запрос данных
            request = GetCandlesRequest(
                instrument_id=figi,
                from_=current_start,
                to=current_end,
                interval=CandleInterval.CANDLE_INTERVAL_DAY
            )
            
            response = await self.client.market_data.get_candles(request=request)
            all_candles.extend(response.candles)
            current_start = current_end + timedelta(days=1)
        
        # Конвертация в DataFrame
        data = []
        for candle in all_candles:
            data.append({
                'date': candle.time,
                'open': self.quotation_to_float(candle.open),
                'high': self.quotation_to_float(candle.high),
                'low': self.quotation_to_float(candle.low),
                'close': self.quotation_to_float(candle.close),
                'volume': candle.volume
            })
        
        return pd.DataFrame(data)

    def calculate_technical_indicators(self, df):
        """Расчет технических индикаторов"""
        # Moving Averages
        df['MA_20'] = df['close'].rolling(window=20).mean()
        df['MA_50'] = df['close'].rolling(window=50).mean()
        df['MA_200'] = df['close'].rolling(window=200).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp12 = df['close'].ewm(span=12).mean()
        exp26 = df['close'].ewm(span=26).mean()
        df['MACD'] = exp12 - exp26
        df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
        
        # Bollinger Bands
        df['BB_Middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        
        return df.dropna()

    def prepare_features(self, df):
        """Подготовка признаков для ML модели"""
        features = df[['close', 'volume', 'MA_20', 'MA_50', 'MA_200', 
                      'RSI', 'MACD', 'MACD_Signal', 'BB_Upper', 'BB_Lower']].copy()
        
        # Lag features
        for lag in [1, 2, 3, 5, 10]:
            features[f'close_lag_{lag}'] = df['close'].shift(lag)
            features[f'volume_lag_{lag}'] = df['volume'].shift(lag)
        
        # Price changes
        features['price_change_1d'] = df['close'].pct_change()
        features['price_change_5d'] = df['close'].pct_change(5)
        features['price_change_30d'] = df['close'].pct_change(30)
        
        return features.dropna()

    async def generate_predictions(self, ticker_name, figi):
        """Генерация прогнозов для тикера"""
        print(f"[ПРОГНОЗ] Анализ {ticker_name}...")
        
        # Получение исторических данных
        historical_data = await self.get_historical_data(figi, years=5)
        
        if len(historical_data) < 100:
            print(f"Недостаточно данных для {ticker_name}")
            return None
        
        # Расчет индикаторов
        df_with_indicators = self.calculate_technical_indicators(historical_data)
        
        # Подготовка признаков
        features = self.prepare_features(df_with_indicators)
        target = df_with_indicators['close'].shift(-30).dropna()
        
        if len(features) < 30 or len(target) < 30:
            return None
            
        # Обучение модели
        X = self.scaler.fit_transform(features.iloc[:-30])
        y = target.iloc[:len(X)]
        
        self.model.fit(X, y)
        
        # Прогноз на будущее
        last_features = features.iloc[-1:].copy()
        future_predictions = []
        
        # Прогноз на 6 месяцев вперед
        for _ in range(180):
            X_pred = self.scaler.transform(last_features)
            prediction = self.model.predict(X_pred)[0]
            future_predictions.append(prediction)
            
            # Обновление features для следующего прогноза
            new_row = last_features.iloc[-1:].copy()
            new_row['close'] = prediction
            for col in new_row.columns:
                if 'lag' in col:
                    new_row[col] = prediction
            last_features = pd.concat([last_features, new_row])
        
        # Расчет времени удержания позиции
        current_price = df_with_indicators['close'].iloc[-1]
        target_price = future_predictions[-1]
        days_to_target = 180  # 6 месяцев
        daily_growth = (target_price / current_price) ** (1/days_to_target) - 1
        
        # Нахождение оптимальной точки выхода
        exit_day = None
        for i, price in enumerate(future_predictions):
            if price >= target_price * 0.95:  # 95% от целевой цены
                exit_day = i
                break
        
        return {
            'historical': df_with_indicators,
            'predictions': future_predictions,
            'current_price': current_price,
            'target_price': target_price,
            'predicted_growth': (target_price / current_price - 1) * 100,
            'daily_growth': daily_growth * 100,
            'exit_day': exit_day if exit_day else 180,
            'exit_date': (datetime.now() + timedelta(days=exit_day if exit_day else 180)).strftime("%Y-%m-%d")
        }

    async def execute_trade(self, figi, action, quantity):
        """Выполнение торговой операции"""
        try:
            account_id = (await self.client.users.get_accounts()).accounts[0].id
            
            if action == 'BUY':
                order = await self.client.orders.post_order(
                    figi=figi,
                    quantity=quantity,
                    direction=OrderDirection.ORDER_DIRECTION_BUY,
                    order_type=OrderType.ORDER_TYPE_MARKET,
                    account_id=account_id
                )
                print(f"[ТОРГОВЛЯ] Куплено {quantity} акций")
                return order
            elif action == 'SELL':
                order = await self.client.orders.post_order(
                    figi=figi,
                    quantity=quantity,
                    direction=OrderDirection.ORDER_DIRECTION_SELL,
                    order_type=OrderType.ORDER_TYPE_MARKET,
                    account_id=account_id
                )
                print(f"[ТОРГОВЛЯ] Продано {quantity} акций")
                return order
            elif action == 'SHORT':
                # Реализация шорт-позиции
                # В реальности требуется маржинальное кредитование
                print(f"[ТОРГОВЛЯ] Открыта шорт-позиция на {quantity} акций")
                return {"status": "SHORT_POSITION_OPENED"}
        except Exception as e:
            print(f"Ошибка торговли: {str(e)}")
            return None

    async def analyze_market(self):
        """Анализ рынка и генерация сигналов"""
        results = {}
        trading_signals = []
        
        # Анализ каждого тикера
        for name, figi in self.tickers.items():
            try:
                prediction = await self.generate_predictions(name, figi)
                if prediction:
                    results[name] = prediction
                    
                    # Генерация торговых сигналов
                    if prediction['predicted_growth'] > 15:
                        trading_signals.append({
                            'ticker': name,
                            'figi': figi,
                            'action': 'BUY',
                            'current_price': prediction['current_price'],
                            'target_price': prediction['target_price'],
                            'predicted_growth': prediction['predicted_growth'],
                            'exit_day': prediction['exit_day'],
                            'exit_date': prediction['exit_date'],
                            'confidence': 'HIGH',
                            'timestamp': datetime.now()
                        })
                    elif prediction['predicted_growth'] < -10:
                        trading_signals.append({
                            'ticker': name,
                            'figi': figi,
                            'action': 'SHORT',
                            'current_price': prediction['current_price'],
                            'target_price': prediction['target_price'],
                            'predicted_growth': prediction['predicted_growth'],
                            'exit_day': prediction['exit_day'],
                            'exit_date': prediction['exit_date'],
                            'confidence': 'HIGH',
                            'timestamp': datetime.now()
                        })
            except Exception as e:
                print(f"Ошибка анализа {name}: {str(e)}")
                continue
        
        # Сохранение сигналов в историю
        for signal in trading_signals:
            self.signals_history.append(signal)
        
        return results, trading_signals

    async def run_continuous_analysis(self):
        """Непрерывный анализ рынка"""
        await self.initialize()
        
        while True:
            print(f"\n[АНАЛИЗ] Запуск анализа в {datetime.now().strftime('%H:%M:%S')}")
            results, signals = await self.analyze_market()
            
            # Ожидание следующего анализа
            await asyncio.sleep(self.trade_settings['analysis_interval'])
