"""
Основной модуль проверки кошельков с асинхронной оптимизацией.
"""
import os
import time
import random
import threading
import asyncio
import json
import concurrent.futures
from datetime import datetime
from config import Config
from crypto_utils import mnemonic_to_seed, derive_eth_address, derive_btc_address, generate_human_mnemonic, heuristic_score
from crypto_utils import cached_mnemonic_to_seed, cached_derive_eth_address, cached_derive_btc_address
from api_client import check_balances_batch_async
from known_wallets import known_wallets_db
from optimized_executor import optimized_executor

class WalletChecker:
    """Класс для асинхронной проверки кошельков на наличие средств"""
    
    def __init__(self, wordlists, gui_callback=None):
        self.checked_count = 0
        self.found_count = 0
        self.wordlists = wordlists
        self.gui_callback = gui_callback
        self.is_running = False
        self.lock = threading.Lock()
        self.pattern_index = 0
        self.common_patterns = self.load_common_patterns()
        self.start_time = None
        self.last_update_time = None
        self.last_checked_count = 0
        self.last_stats_time = None
        
    def load_common_patterns(self):
        """Загрузка распространенных паттернов"""
        patterns = []
        
        try:
            with open(Config.COMMON_PASSWORDS_FILE, "r", encoding="utf-8") as f:
                patterns.extend([line.strip() for line in f.readlines() if len(line.strip()) >= 8])
        except:
            pass
        
        try:
            with open(Config.KNOWN_PHRASES_FILE, "r", encoding="utf-8") as f:
                patterns.extend([line.strip() for line in f.readlines() if len(line.split()) >= 10])
        except:
            pass
        
        return patterns
    
    def generate_mnemonic(self, lang):
        """Генерация мнемонической фразы BIP-39 без повторяющихся слов"""
        if lang not in self.wordlists:
            return None
        
        wordlist = self.wordlists[lang]
        
        # Всегда используем случайную выборку без повторений (правильная BIP-39)
        return ' '.join(random.sample(wordlist, Config.MNEMONIC_LENGTH))
    
    def generate_mnemonics_batch(self, count):
        """Пакетная генерация мнемонических фраз"""
        batch = []
        for _ in range(count):
            if Config.ENABLED_LANGUAGES:
                lang = random.choice(Config.ENABLED_LANGUAGES)
            else:
                lang = random.choice(list(self.wordlists.keys()))
            
            mnemonic = self.generate_mnemonic(lang)
            if mnemonic:
                batch.append((lang, mnemonic))
        
        return batch
    
    def validate_mnemonic(self, lang, mnemonic):
        """Проверка валидности мнемонической фразы"""
        # Проверяем что слова не повторяются
        words = mnemonic.split()
        if len(words) != len(set(words)):
            return False
        
        # Проверяем что все слова из правильного словаря
        if lang not in self.wordlists:
            return False
            
        wordlist = self.wordlists[lang]
        if not all(word in wordlist for word in words):
            return False
        
        # Проверяем правильную длину
        if len(words) != Config.MNEMONIC_LENGTH:
            return False
            
        return True
    
    def prefilter_batch(self, batch):
        """Оптимизированная предварительная фильтрация пакета"""
        if not Config.USE_PREFILTERING:
            return batch
            
        filtered = []
        
        for lang, mnemonic in batch:
            # Сначала проверяем базовую валидность
            if not self.validate_mnemonic(lang, mnemonic):
                continue
                
            try:
                seed = cached_mnemonic_to_seed(mnemonic, "")
                eth_address = cached_derive_eth_address(seed)
                
                # Применяем эвристики для фильтрации
                score = heuristic_score(eth_address)
                if score >= Config.PREFILTER_THRESHOLD:
                    filtered.append((lang, mnemonic))
            except:
                continue
        
        return filtered
    
    def check_wallet(self, wallet_data):
        """Синхронная проверка кошелька (обертка для асинхронной)"""
        lang, mnemonic = wallet_data
        
        # Проверяем валидность мнемонической фразы
        if not self.validate_mnemonic(lang, mnemonic):
            return None
            
        try:
            seed = cached_mnemonic_to_seed(mnemonic, "")
            
            eth_address = cached_derive_eth_address(seed)
            btc_address = cached_derive_btc_address(seed)
            
            # Пропускаем проверку, если адрес уже известен
            if known_wallets_db.is_known(eth_address) or known_wallets_db.is_known(btc_address):
                return None
            
            addresses = {"eth": eth_address, "btc": btc_address}
            
            # Запускаем асинхронную проверку балансов
            future = check_balances_batch_async(addresses)
            balance_data = future.result(timeout=Config.REQUEST_TIMEOUT * 2)
            
            total_balance_usd = balance_data['total_usd']
            
            # Если включена проверка активности, проверяем минимальное количество транзакций
            if Config.USE_TX_ACTIVITY_CHECK:
                has_activity = False
                for currency, tx_count in balance_data['tx_activity'].items():
                    if tx_count >= Config.MIN_TX_COUNT:
                        has_activity = True
                        break
                
                # Если нет активности и баланс незначительный, пропускаем
                if not has_activity and total_balance_usd < Config.MIN_TOTAL_BALANCE_USD * 5:
                    return None
            
            if total_balance_usd >= Config.MIN_TOTAL_BALANCE_USD:
                # Добавляем в базу известных кошельков
                known_wallets_db.add_wallet(eth_address, total_balance_usd)
                known_wallets_db.add_wallet(btc_address, total_balance_usd)
                
                return {
                    'mnemonic': mnemonic,
                    'language': lang,
                    'eth_address': eth_address,
                    'btc_address': btc_address,
                    'crypto_balances': balance_data['crypto_balances'],
                    'usd_balances': balance_data['usd_balances'],
                    'total_balance_usd': total_balance_usd,
                    'tx_activity': balance_data.get('tx_activity', {}),
                    'timestamp': datetime.now().isoformat()
                }
            
            return None
        except Exception as e:
            return None
    
    def save_results(self, result):
        """Сохранение результатов в файл"""
        filename = f"{Config.RESULTS_DIR}/wallet_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        return filename
    
    def prioritize_wallets(self, wallet_list):
        """Приоритизация кошельков для проверки на основе эвристик"""
        prioritized = []
        for lang, mnemonic in wallet_list:
            try:
                seed = cached_mnemonic_to_seed(mnemonic, "")
                eth_address = cached_derive_eth_address(seed)
                score = heuristic_score(eth_address)
                prioritized.append((score, lang, mnemonic))
            except:
                continue
        
        prioritized.sort(key=lambda x: x[0], reverse=True)
        return [(lang, mnemonic) for _, lang, mnemonic in prioritized]
    
    def process_batch_optimized(self, batch):
        """Оптимизированная обработка пакета"""
        # Предварительная фильтрация
        if Config.USE_PREFILTERING:
            batch = self.prefilter_batch(batch)
        
        # Пакетная проверка кошельков
        with concurrent.futures.ThreadPoolExecutor(max_workers=Config.MAX_WORKERS) as executor:
            results = list(executor.map(self.check_wallet, batch))
        
        # Обработка результатов
        valid_results = [r for r in results if r is not None]
        
        with self.lock:
            self.checked_count += len(batch)
            self.found_count += len(valid_results)
        
        return valid_results
    
    def run_continuous_optimized(self):
        """Оптимизированный непрерывный запуск процесса проверки"""
        self.is_running = True
        self.start_time = time.time()
        self.last_update_time = time.time()
        self.last_checked_count = 0
        self.last_stats_time = None
        
        # Запускаем исполнитель
        optimized_executor.start()
        
        try:
            # Основной цикл проверки
            while self.is_running:
                try:
                    # Генерируем большой пакет мнемонических фраз
                    batch = self.generate_mnemonics_batch(Config.BATCH_SIZE)
                    
                    if not batch:
                        time.sleep(0.01)
                        continue
                    
                    # Обрабатываем пакет
                    results = self.process_batch_optimized(batch)
                    
                    # Обрабатываем результаты
                    for result in results:
                        filename = self.save_results(result)
                        
                        if self.gui_callback:
                            self.gui_callback({
                                'type': 'found',
                                'result': result,
                                'filename': filename
                            })
                    
                    # Обновляем статистику
                    current_time = time.time()
                    if self.last_stats_time is None or current_time - self.last_stats_time > 0.5:
                        self.last_stats_time = current_time
                        
                        # Рассчитываем скорость
                        speed = 0
                        if self.last_update_time:
                            time_diff = current_time - self.last_update_time
                            count_diff = self.checked_count - self.last_checked_count
                            if time_diff > 0:
                                speed = count_diff / time_diff
                        
                        self.last_update_time = current_time
                        self.last_checked_count = self.checked_count
                        
                        if self.gui_callback:
                            self.gui_callback({
                                'type': 'stats',
                                'checked': self.checked_count,
                                'found': self.found_count,
                                'speed': speed,
                                'status': f'Проверка кошельков...'
                            })
                    
                    # Короткая пауза
                    time.sleep(0.001)
                    
                except Exception as e:
                    print(f"Ошибка в основном цикле: {e}")
                    time.sleep(0.1)
                    
        finally:
            # Останавливаем исполнитель
            optimized_executor.stop()
        
        elapsed_time = time.time() - self.start_time
        print("=" * 50)
        print(f"Проверка завершена за {elapsed_time:.2f} секунд")
        print(f"Проверено кошельков: {self.checked_count}")
        print(f"Найдено подходящих: {self.found_count}")
        
        if self.gui_callback:
            self.gui_callback({
                'type': 'finished',
                'checked': self.checked_count,
                'found': self.found_count,
                'elapsed_time': elapsed_time
            })
    
    def run_continuous(self):
        """Алиас для обратной совместимости"""
        self.run_continuous_optimized()
    
    def stop(self):
        """Остановка проверки"""
        self.is_running = False
