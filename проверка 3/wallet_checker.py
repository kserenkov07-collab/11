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
import requests
from datetime import datetime
from config import Config
from crypto_utils import mnemonic_to_seed, derive_eth_address, derive_btc_address, generate_human_mnemonic
from crypto_utils import cached_mnemonic_to_seed, cached_derive_eth_address, cached_derive_btc_address
from crypto_utils import cached_derive_ltc_address, cached_derive_xrp_address, cached_derive_bch_address, cached_derive_doge_address
from crypto_utils import enhanced_heuristic_score, assess_mnemonic_quality
from api_client import check_balances_batch_async, get_primary_balances_batch
from known_wallets import known_wallets_db
from optimized_executor import optimized_executor
from logger import logger

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
        
        logger.info("Инициализация WalletChecker завершена")
        
    def load_common_patterns(self):
        """Загрузка распространенных паттернов"""
        patterns = []
        
        try:
            with open(Config.COMMON_PASSWORDS_FILE, "r", encoding="utf-8") as f:
                patterns.extend([line.strip() for line in f.readlines() if len(line.strip()) >= 8])
            logger.info(f"Загружено {len(patterns)} паттернов из common_passwords.txt")
        except Exception as e:
            logger.error(f"Ошибка загрузки common_passwords.txt: {e}")
        
        try:
            with open(Config.KNOWN_PHRASES_FILE, "r", encoding="utf-8") as f:
                patterns.extend([line.strip() for line in f.readlines() if len(line.split()) >= 10])
            logger.info(f"Загружено {len(patterns)} паттернов из known_phrases.txt")
        except Exception as e:
            logger.error(f"Ошибка загрузки known_phrases.txt: {e}")
        
        try:
            with open(Config.CRYPTO_PATTERNS_FILE, "r", encoding="utf-8") as f:
                patterns.extend([line.strip() for line in f.readlines() if line.strip()])
            logger.info(f"Загружено {len(patterns)} паттернов из crypto_patterns.txt")
        except Exception as e:
            logger.error(f"Ошибка загрузки crypto_patterns.txt: {e}")
        
        return patterns
    
    def generate_valid_mnemonics_batch(self, count):
        """Генерация только валидных мнемонических фраз"""
        batch = []
        attempts = 0
        max_attempts = count * 3  # Ограничиваем количество попыток
        
        while len(batch) < count and attempts < max_attempts:
            attempts += 1
            
            if Config.USE_HUMAN_PATTERNS:
                lang = random.choice(Config.ENABLED_LANGUAGES)
                human_patterns = self.load_common_patterns()
                
                if human_patterns and random.random() < 0.7:
                    pattern = random.choice(human_patterns)
                    words = pattern.split()[:Config.MNEMONIC_LENGTH]
                    
                    # Фильтруем слова, оставляя только valid
                    valid_words = [word for word in words if word in self.wordlists[lang]]
                    
                    if len(valid_words) >= Config.MNEMONIC_LENGTH * 0.8:  # Минимум 80% valid слов
                        # Дополняем до нужной длины
                        if len(valid_words) < Config.MNEMONIC_LENGTH:
                            additional = random.sample(
                                [w for w in self.wordlists[lang] if w not in valid_words],
                                Config.MNEMONIC_LENGTH - len(valid_words)
                            )
                            valid_words.extend(additional)
                        
                        mnemonic = ' '.join(valid_words)
                        if self.validate_mnemonic(lang, mnemonic):
                            batch.append((lang, mnemonic))
                            continue
            
            # Стандартная генерация
            lang = random.choice(Config.ENABLED_LANGUAGES)
            mnemonic = ' '.join(random.sample(self.wordlists[lang], Config.MNEMONIC_LENGTH))
            
            if self.validate_mnemonic(lang, mnemonic):
                batch.append((lang, mnemonic))
        
        return batch
    
    def generate_mnemonic(self, lang):
        """Генерация мнемонической фразы BIP-39 без повторяющихся слов"""
        if lang not in self.wordlists:
            logger.warning(f"Словарь для языка {lang} не найден")
            return None
        
        wordlist = self.wordlists[lang]
        
        # Всегда используем случайную выборку без повторений (правильная BIP-39)
        mnemonic = ' '.join(random.sample(wordlist, Config.MNEMONIC_LENGTH))
        logger.debug(f"Сгенерирована мнемоническая фраза: {mnemonic} (язык: {lang})")
        return mnemonic
    
    def generate_prioritized_mnemonics(self, count):
        """Генерация мнемонических фраз с приоритетом на человеческие паттерны"""
        batch = []
        human_patterns = self.load_common_patterns()
        
        for _ in range(count):
            lang = random.choice(Config.ENABLED_LANGUAGES)
            
            # 70% chance to use human-like patterns
            if Config.USE_HUMAN_PATTERNS and random.random() < 0.7 and human_patterns:
                pattern = random.choice(human_patterns)
                words = pattern.split()[:Config.MNEMONIC_LENGTH]
                
                # Fill remaining words if needed
                if len(words) < Config.MNEMONIC_LENGTH:
                    additional_words = random.sample(
                        [w for w in self.wordlists[lang] if w not in words],
                        Config.MNEMONIC_LENGTH - len(words)
                    )
                    words.extend(additional_words)
                
                mnemonic = ' '.join(words)
            else:
                # Standard BIP-39 generation
                mnemonic = ' '.join(random.sample(self.wordlists[lang], Config.MNEMONIC_LENGTH))
            
            batch.append((lang, mnemonic))
        
        logger.info(f"Сгенерировано {len(batch)} мнемонических фраз с приоритизацией")
        return batch
    
    def generate_mnemonics_batch(self, count):
        """Пакетная генерация мнемонических фраз"""
        if Config.USE_HUMAN_PATTERNS:
            return self.generate_prioritized_mnemonics(count)
        
        return self.generate_valid_mnemonics_batch(count)
    
    def validate_mnemonic(self, lang, mnemonic):
        """Проверка валидности мнемонической фразы"""
        # Проверяем что слова не повторяются
        words = mnemonic.split()
        if len(words) != len(set(words)):
            logger.debug(f"Мнемоническая фраза содержит повторяющиеся слова: {mnemonic}")
            return False
        
        # Проверяем что все слова из правильного словаря
        if lang not in self.wordlists:
            logger.warning(f"Словарь для языка {lang} не найден")
            return False
            
        wordlist = self.wordlists[lang]
        invalid_words = [word for word in words if word not in wordlist]
        if invalid_words:
            logger.debug(f"Мнемоническая фраза содержит невалидные слова: {invalid_words}")
            return False
        
        # Проверяем правильную длину
        if len(words) != Config.MNEMONIC_LENGTH:
            logger.debug(f"Неправильная длина мнемонической фразы: {len(words)} вместо {Config.MNEMONIC_LENGTH}")
            return False
            
        logger.debug(f"Мнемоническая фраза валидна: {mnemonic}")
        return True
    
    def adaptive_prefilter_threshold(self):
        """Адаптивный расчет порога фильтрации на основе скорости нахождения кошельков"""
        if not Config.ADAPTIVE_FILTERING:
            return Config.PREFILTER_THRESHOLD
        
        # Если мы находим много кошельков, увеличиваем порог для большей selectivity
        if self.found_count > 0 and self.checked_count > 0:
            found_ratio = self.found_count / self.checked_count
            if found_ratio > 0.01:  # 1% успешных проверок
                new_threshold = min(
                    Config.MAX_PREFILTER_THRESHOLD,
                    Config.PREFILTER_THRESHOLD + Config.FILTER_ADJUSTMENT_STEP
                )
                logger.info(f"Увеличиваем порог фильтрации с {Config.PREFILTER_THRESHOLD} до {new_threshold}")
                return new_threshold
            elif found_ratio < 0.001:  # 0.1% успешных проверок
                new_threshold = max(
                    Config.MIN_PREFILTER_THRESHOLD,
                    Config.PREFILTER_THRESHOLD - Config.FILTER_ADJUSTMENT_STEP
                )
                logger.info(f"Уменьшаем порог фильтрации с {Config.PREFILTER_THRESHOLD} до {new_threshold}")
                return new_threshold
        
        return Config.PREFILTER_THRESHOLD
    
    def enhanced_prefilter_batch(self, batch):
        """Расширенная предварительная фильтрация с оценкой мнемонических фраз"""
        if not Config.USE_PREFILTERING:
            return batch
            
        filtered = []
        current_threshold = self.adaptive_prefilter_threshold()
        
        for lang, mnemonic in batch:
            # Сначала проверяем базовую валидность
            if not self.validate_mnemonic(lang, mnemonic):
                continue
                
            try:
                seed = cached_mnemonic_to_seed(mnemonic, "")
                eth_address = cached_derive_eth_address(seed)
                
                # Комплексная оценка
                address_score = enhanced_heuristic_score(eth_address, mnemonic)
                mnemonic_score = assess_mnemonic_quality(mnemonic)
                total_score = address_score + mnemonic_score
                
                if total_score >= current_threshold:
                    filtered.append((lang, mnemonic, total_score))  # Store with score for prioritization
            except Exception as e:
                logger.error(f"Ошибка при предварительной фильтрации: {e}")
                continue
        
        # Сортируем по оценке для приоритетной обработки
        filtered.sort(key=lambda x: x[2], reverse=True)
        logger.info(f"После предварительной фильтрации осталось {len(filtered)} мнемонических фраз")
        return [(lang, mnemonic) for lang, mnemonic, score in filtered]
    
    def prefilter_batch(self, batch):
        """Предварительная фильтрация пакета с помощью эвристик"""
        if not Config.USE_PREFILTERING:
            return batch
            
        return self.enhanced_prefilter_batch(batch)
    
    def get_single_balance_sync(self, currency, address):
        """Синхронное получение баланса для одной валюты"""
        try:
            logger.debug(f"Проверка баланса {currency} для адреса: {address}")
            
            # Используем первый доступный API URL
            api_url = Config.CRYPTOCURRENCIES[currency]["api_urls"][0]
            url = api_url.format(address)
            
            response = requests.get(url, timeout=Config.PRIMARY_CHECK_TIMEOUT)
            if response.status_code == 200:
                if currency == "BTC":
                    balance = int(response.text) / 10**8
                elif currency == "ETH":
                    data = response.json()
                    balance = data.get('balance', 0) / 10**8
                elif currency == "LTC":
                    data = response.json()
                    balance = data.get('balance', 0) / 10**8
                else:
                    balance = 0
                    
                logger.debug(f"Баланс {currency}: {balance}")
                return balance
                
            return 0
        except Exception as e:
            logger.error(f"Ошибка при проверке баланса {currency}: {e}")
            return 0
    
    def check_wallet_optimized(self, wallet_data):
        """Оптимизированная проверка кошелька с двухэтапной проверкой баланса"""
        lang, mnemonic = wallet_data
        
        logger.info(f"Начинаем проверку кошелька: {mnemonic[:20]}... (язык: {lang})")
        
        if not self.validate_mnemonic(lang, mnemonic):
            logger.debug("Мнемоническая фраза не прошла валидацию")
            return None
            
        try:
            seed = cached_mnemonic_to_seed(mnemonic, "")
            logger.debug("Мнемоническая фраза преобразована в seed")
            
            eth_address = cached_derive_eth_address(seed)
            btc_address = cached_derive_btc_address(seed)
            ltc_address = cached_derive_ltc_address(seed)
            xrp_address = cached_derive_xrp_address(seed)
            bch_address = cached_derive_bch_address(seed)
            doge_address = cached_derive_doge_address(seed)
            
            logger.debug(f"Сгенерированы адреса - ETH: {eth_address}, BTC: {btc_address}, LTC: {ltc_address}")
            
            # Быстрая проверка по известным кошелькам
            if (known_wallets_db.is_known(eth_address) or known_wallets_db.is_known(btc_address) or
                known_wallets_db.is_known(ltc_address) or known_wallets_db.is_known(xrp_address) or
                known_wallets_db.is_known(bch_address) or known_wallets_db.is_known(doge_address)):
                logger.debug("Кошелек уже известен, пропускаем проверку")
                return None
            
            # Первый этап: проверяем только BTC, ETH и LTC
            primary_currencies = Config.PRIMARY_CURRENCIES
            primary_balances = {}
            primary_usd_total = 0
            
            # Получаем актуальные курсы валют из конфига
            btc_rate = Config.exchange_rates.get('BTC', 50000)
            eth_rate = Config.exchange_rates.get('ETH', 3000)
            ltc_rate = Config.exchange_rates.get('LTC', 150)
            
            # Проверяем баланс BTC
            btc_balance = self.get_single_balance_sync("BTC", btc_address)
            primary_balances["BTC"] = btc_balance
            primary_usd_total += btc_balance * btc_rate
            
            # Проверяем баланс ETH
            eth_balance = self.get_single_balance_sync("ETH", eth_address)
            primary_balances["ETH"] = eth_balance
            primary_usd_total += eth_balance * eth_rate
            
            # Проверяем баланс LTC
            ltc_balance = self.get_single_balance_sync("LTC", ltc_address)
            primary_balances["LTC"] = ltc_balance
            primary_usd_total += ltc_balance * ltc_rate
            
            logger.debug(f"Первичная проверка: BTC={btc_balance}, ETH={eth_balance}, LTC={ltc_balance}, Total USD={primary_usd_total}")
            
            # Если баланс основных валют не превышает порог, пропускаем кошелек
            if primary_usd_total < Config.MIN_PRIMARY_BALANCE_USD:
                logger.debug("Баланс основных валют ниже порога, пропускаем кошелек")
                return None
            
            logger.debug("Баланс основных валут превышает порог, продолжаем проверку")
            
            # Второй этап: проверяем все остальные валюты
            addresses = {
                "eth": eth_address, 
                "btc": btc_address,
                "ltc": ltc_address,
                "xrp": xrp_address,
                "bch": bch_address,
                "doge": doge_address
            }
            logger.debug("Начинаем проверку всех валют")
            balance_data = check_balances_batch_async(addresses).result()
            
            # Добавляем результаты первичной проверки к общим данным
            balance_data['crypto_balances'].update(primary_balances)
            balance_data['usd_balances']['BTC'] = btc_balance * btc_rate
            balance_data['usd_balances']['ETH'] = eth_balance * eth_rate
            balance_data['usd_balances']['LTC'] = ltc_balance * ltc_rate
            balance_data['total_usd'] = sum(balance_data['usd_balances'].values())
            
            logger.debug(f"Полная проверка: Total USD={balance_data['total_usd']}")
            
            if balance_data['total_usd'] >= Config.MIN_TOTAL_BALANCE_USD:
                # Добавляем в базу известных кошельков
                known_wallets_db.add_wallet(eth_address, balance_data['total_usd'])
                known_wallets_db.add_wallet(btc_address, balance_data['total_usd'])
                known_wallets_db.add_wallet(ltc_address, balance_data['total_usd'])
                
                logger.info(f"Найден кошелек с балансом! Total USD: {balance_data['total_usd']}")
                
                return {
                    'mnemonic': mnemonic,
                    'language': lang,
                    'eth_address': eth_address,
                    'btc_address': btc_address,
                    'ltc_address': ltc_address,
                    'xrp_address': xrp_address,
                    'bch_address': bch_address,
                    'doge_address': doge_address,
                    'crypto_balances': balance_data['crypto_balances'],
                    'usd_balances': balance_data['usd_balances'],
                    'total_balance_usd': balance_data['total_usd'],
                    'tx_activity': balance_data.get('tx_activity', {}),
                    'timestamp': datetime.now().isoformat()
                }
            
            logger.debug("Общий баланс ниже минимального порога")
            return None
        except Exception as e:
            logger.error(f"Ошибка при проверке кошелька: {e}")
            return None
    
    def check_wallet(self, wallet_data):
        """Синхронная проверка кошелька (обертка для асинхронной)"""
        if Config.USE_PRIORITIZATION:
            return self.check_wallet_optimized(wallet_data)
            
        lang, mnemonic = wallet_data
        
        # Проверяем валидность мнемонической фразы
        if not self.validate_mnemonic(lang, mnemonic):
            return None
            
        try:
            seed = cached_mnemonic_to_seed(mnemonic, "")
            
            eth_address = cached_derive_eth_address(seed)
            btc_address = cached_derive_btc_address(seed)
            ltc_address = cached_derive_ltc_address(seed)
            xrp_address = cached_derive_xrp_address(seed)
            bch_address = cached_derive_bch_address(seed)
            doge_address = cached_derive_doge_address(seed)
            
            # Пропускаем проверку, если адрес уже известен
            if (known_wallets_db.is_known(eth_address) or known_wallets_db.is_known(btc_address) or
                known_wallets_db.is_known(ltc_address) or known_wallets_db.is_known(xrp_address) or
                known_wallets_db.is_known(bch_address) or known_wallets_db.is_known(doge_address)):
                return None
            
            addresses = {
                "eth": eth_address, 
                "btc": btc_address,
                "ltc": ltc_address,
                "xrp": xrp_address,
                "bch": bch_address,
                "doge": doge_address
            }
            
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
                known_wallets_db.add_wallet(ltc_address, total_balance_usd)
                
                return {
                    'mnemonic': mnemonic,
                    'language': lang,
                    'eth_address': eth_address,
                    'btc_address': btc_address,
                    'ltc_address': ltc_address,
                    'xrp_address': xrp_address,
                    'bch_address': bch_address,
                    'doge_address': doge_address,
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
        
        logger.info(f"Результаты сохранены в файл: {filename}")
        return filename
    
    def prioritize_wallets(self, wallet_list):
        """Приоритизация кошельков для проверки на основе эвристик"""
        prioritized = []
        for lang, mnemonic in wallet_list:
            try:
                seed = cached_mnemonic_to_seed(mnemonic, "")
                eth_address = cached_derive_eth_address(seed)
                score = enhanced_heuristic_score(eth_address, mnemonic)
                prioritized.append((score, lang, mnemonic))
            except Exception as e:
                logger.error(f"Ошибка при приоритизации: {e}")
                continue
        
        prioritized.sort(key=lambda x: x[0], reverse=True)
        logger.info(f"Приоритизация завершена, обработано {len(prioritized)} мнемонических фраз")
        return [(lang, mnemonic) for _, lang, mnemonic in prioritized]
    
    def process_batch_optimized(self, batch):
        """Оптимизированная обработка пакета"""
        logger.info(f"Начинаем обработку пакета из {len(batch)} мнемонических фраз")
        
        # Предварительная фильтрация
        if Config.USE_PREFILTERING:
            logger.debug("Применяем предварительную фильтрации")
            batch = self.prefilter_batch(batch)
            logger.debug(f"После предварительной фильтрации осталось {len(batch)} фраз")
        
        # Приоритизация
        if Config.USE_PRIORITIZATION:
            logger.debug("Применяем приоритизацию")
            batch = self.prioritize_wallets(batch)
        
        # Разделяем пакет на подпакеты для параллельной обработки
        sub_batches = [batch[i:i + Config.MAX_WORKERS] for i in range(0, len(batch), Config.MAX_WORKERS)]
        valid_results = []
        
        for sub_batch in sub_batches:
            # Параллельная проверка подпакета
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(sub_batch)) as executor:
                futures = {executor.submit(self.check_wallet, wallet_data): wallet_data for wallet_data in sub_batch}
                
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result is not None:
                        valid_results.append(result)
            
            # Обновляем статистику после каждого подпакета
            with self.lock:
                self.checked_count += len(sub_batch)
                self.found_count += len(valid_results)
            
            # Проверяем флаг остановки
            if not self.is_running:
                break
        
        logger.info(f"Пакет обработан: проверено {len(batch)}, найдено {len(valid_results)}")
        return valid_results
    
    def run_continuous_optimized(self):
        """Оптимизированный непрерывный запуск процесса проверки"""
        self.is_running = True
        self.start_time = time.time()
        self.last_update_time = time.time()
        self.last_checked_count = 0
        self.last_stats_time = None
        
        logger.info("Запуск непрерывной проверки кошельков")
        
        # Запускаем исполнитель
        optimized_executor.start()
        
        try:
            # Основной цикл проверки
            while self.is_running:
                try:
                    # Генерируем большой пакет мнемонических фраз
                    batch = self.generate_mnemonics_batch(Config.BATCH_SIZE)
                    
                    if not batch:
                        logger.debug("Не удалось сгенерировать пакет мнемонических фраз")
                        time.sleep(0.01)
                        continue
                    
                    logger.debug(f"Сгенерирован пакет из {len(batch)} мнемонических фраз")
                    
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
                    logger.error(f"Ошибка в основном цикле: {e}")
                    time.sleep(0.1)
                    
        finally:
            # Останавливаем исполнитель
            optimized_executor.stop()
        
        elapsed_time = time.time() - self.start_time
        logger.info(f"Проверка завершена за {elapsed_time:.2f} секунд")
        logger.info(f"Проверено кошельков: {self.checked_count}")
        logger.info(f"Найдено подходящих: {self.found_count}")
        
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
        logger.info("Проверка кошельков остановлена")
