# mathematical_analysis.py
# МОДУЛЬ МАТЕМАТИЧЕСКОГО АНАЛИЗА С ИСПОЛЬЗОВАНИЕМ SYMPY И SCIPY
# Автор: Колин для выживания деревни

import numpy as np
import scipy
from scipy import optimize, stats, interpolate
import sympy as sp
from sympy import symbols, diff, integrate, Eq, solve
import pandas as pd
from datetime import datetime, timedelta

class MathematicalAnalyzer:
    def __init__(self):
        self.symbolic_vars = {}
        
    def setup_symbolic_analysis(self):
        """Настройка символьных переменных для анализа"""
        # Определение символьных переменных
        t, P, r, sigma = symbols('t P r sigma')
        self.symbolic_vars = {
            't': t,  # время
            'P': P,  # цена
            'r': r,  # процентная ставка
            'sigma': sigma  # волатильность
        }
        
        return t, P, r, sigma
        
    def black_scholes_symbolic(self):
        """Символьный анализ формулы Блэка-Шоулза"""
        t, P, r, sigma = self.setup_symbolic_analysis()
        
        # Формула Блэка-Шоулза для опционов
        d1 = (sp.ln(P) + (r + sigma**2/2)*t) / (sigma * sp.sqrt(t))
        d2 = d1 - sigma * sp.sqrt(t)
        
        # Цена опциона call
        C = P * sp.stats.cdf(d1) - sp.exp(-r*t) * sp.stats.cdf(d2)
        
        # Вычисление греков
        delta = diff(C, P)
        gamma = diff(delta, P)
        theta = diff(C, t)
        vega = diff(C, sigma)
        rho = diff(C, r)
        
        return {
            'formula': C,
            'greeks': {
                'delta': delta,
                'gamma': gamma,
                'theta': theta,
                'vega': vega,
                'rho': rho
            }
        }
        
    def optimize_portfolio(self, returns, covariance_matrix, risk_free_rate=0.05):
        """Оптимизация портфеля с использованием SciPy"""
        n_assets = len(returns)
        
        # Целевая функция: минимизация риска при заданной доходности
        def portfolio_variance(weights):
            return weights.T @ covariance_matrix @ weights
        
        # Ограничения: сумма весов = 1
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        
        # Границы: веса между 0 и 1
        bounds = tuple((0, 1) for _ in range(n_assets))
        
        # Начальное приближение: равные веса
        initial_weights = n_assets * [1. / n_assets]
        
        # Оптимизация
        result = optimize.minimize(
            portfolio_variance, 
            initial_weights, 
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        return result.x
        
    def calculate_var(self, returns, confidence_level=0.95):
        """Расчет Value at Risk с использованием SciPy"""
        # Параметрический метод (нормальное распределение)
        mean = np.mean(returns)
        std = np.std(returns)
        
        # Квантиль нормального распределения
        z_score = stats.norm.ppf(1 - confidence_level)
        
        # Расчет VaR
        var_param = mean + z_score * std
        
        # Исторический метод
        var_historical = np.percentile(returns, (1 - confidence_level) * 100)
        
        return {
            'parametric': var_param,
            'historical': var_historical,
            'mean': mean,
            'std': std
        }
        
    def monte_carlo_simulation(self, initial_price, mu, sigma, days, n_simulations=10000):
        """Монте-Карло симуляция цен с использованием NumPy"""
        # Генерация случайных чисел
        np.random.seed(42)
        
        # Расчет дневной доходности и волатильности
        dt = 1/252  # торговые дни в году
        daily_returns = np.exp((mu - 0.5 * sigma**2) * dt + 
                              sigma * np.sqrt(dt) * np.random.randn(days, n_simulations))
        
        # Симуляция цен
        price_paths = np.zeros_like(daily_returns)
        price_paths[0] = initial_price
        
        for t in range(1, days):
            price_paths[t] = price_paths[t-1] * daily_returns[t]
            
        return price_paths
        
    def interpolate_time_series(self, dates, values, new_dates):
        """Интерполяция временных рядов с использованием SciPy"""
        # Конвертация дат в числовой формат
        numeric_dates = np.array([date.timestamp() for date in dates])
        numeric_new_dates = np.array([date.timestamp() for date in new_dates])
        
        # Интерполяция кубическими сплайнами
        spline = interpolate.CubicSpline(numeric_dates, values)
        interpolated_values = spline(numeric_new_dates)
        
        return interpolated_values
        
    def solve_optimal_timing(self, price_series, transaction_cost=0.001):
        """Решение задачи оптимального времени торговли"""
        # Преобразование в символьные переменные
        t = symbols('t')
        price_func = sp.interpolate(price_series.index, price_series.values)
        
        # Производная для нахождения экстремумов
        derivative = diff(price_func, t)
        
        # Решение уравнения derivative = 0
        critical_points = solve(derivative, t)
        
        # Фильтрация точек в пределах диапазона
        valid_points = [point for point in critical_points if 0 <= point <= len(price_series)-1]
        
        # Добавление конечных точек
        valid_points.extend([0, len(price_series)-1])
        
        # Вычисление значений в критических точках
        values = [price_func.evalf(subs={t: point}) for point in valid_points]
        
        # Учет транзакционных издержек
        net_values = [value * (1 - transaction_cost) for value in values]
        
        # Нахождение оптимальных точек
        buy_idx = np.argmin(net_values)
        sell_idx = np.argmax(net_values)
        
        return {
            'buy_time': valid_points[buy_idx],
            'buy_price': values[buy_idx],
            'sell_time': valid_points[sell_idx],
            'sell_price': values[sell_idx],
            'profit': values[sell_idx] - values[buy_idx] - transaction_cost * (values[buy_idx] + values[sell_idx])
        }
