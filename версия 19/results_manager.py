"""
Модуль для управления результатами проверки кошельков.
"""
import json
import os
import threading
from datetime import datetime
from typing import Dict
from config import config
from logger import logger

class ResultsManager:
    """Менеджер результатов проверки кошельков"""
    
    def __init__(self):
        self.lock = threading.Lock()
        self.ensure_directories()
    
    def ensure_directories(self):
        """Создание необходимых директорий"""
        os.makedirs(config.RESULTS_DIR, exist_ok=True)
        os.makedirs(config.LOGS_DIR, exist_ok=True)
    
    def save_wallet_with_balance(self, mnemonic: str, addresses: Dict, balances: Dict, total_balance: float):
        """Сохранение кошелька с балансом"""
        with self.lock:
            try:
                result_data = {
                    'mnemonic': mnemonic,
                    'addresses': addresses,
                    'balances': balances,
                    'total_balance_usd': total_balance,
                    'timestamp': datetime.now().isoformat()
                }
                
                filename = os.path.join(config.RESULTS_DIR, f"wallets_with_balance_{datetime.now().strftime('%Y%m%d')}.json")
                
                # Загружаем существующие результаты
                existing_results = []
                if os.path.exists(filename):
                    with open(filename, 'r', encoding='utf-8') as f:
                        existing_results = json.load(f)
                
                # Добавляем новый результат
                existing_results.append(result_data)
                
                # Сохраняем обратно
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(existing_results, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Найден кошелек с балансом ${total_balance:.2f}")
                
            except Exception as e:
                logger.error(f"Ошибка сохранения кошелька с балансом: {e}")
    
    def save_empty_wallet(self, mnemonic: str, addresses: Dict):
        """Сохранение пустого кошелька"""
        with self.lock:
            try:
                result_data = {
                    'mnemonic': mnemonic,
                    'addresses': addresses,
                    'timestamp': datetime.now().isoformat()
                }
                
                filename = os.path.join(config.RESULTS_DIR, f"empty_wallets_{datetime.now().strftime('%Y%m%d')}.json")
                
                # Загружаем существующие результаты
                existing_results = []
                if os.path.exists(filename):
                    with open(filename, 'r', encoding='utf-8') as f:
                        existing_results = json.load(f)
                
                # Добавляем новый результат
                existing_results.append(result_data)
                
                # Сохраняем обратно
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(existing_results, f, indent=2, ensure_ascii=False)
                
            except Exception as e:
                logger.error(f"Ошибка сохранения пустого кошелька: {e}")
    
    def export_results(self, format: str = 'json'):
        """Экспорт результатов в различных форматах"""
        # Реализация экспорта в разные форматы
        pass