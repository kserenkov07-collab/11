"""
Модуль для асинхронной работы с API блокчейнов.
Использует aiohttp для максимальной производительности.
"""
import aiohttp
import asyncio
import json
import time
from datetime import datetime
from functools import lru_cache

"""
Конфигурационный модуль с расширенными настройками API и адаптивной фильтрацией.
"""
import os
import json
import multiprocessing

class Config:
    """Класс для управления настройками приложения с расширенными возможностями"""
    
    # Расширенные настройки криптовалют и API
    CRYPTOCURRENCIES = {
        "BTC": {
            "name": "Bitcoin", 
            "api_urls": [
                "https://blockchain.info/q/addressbalance/{}",
                "https://api.blockcypher.com/v1/btc/main/addrs/{}/balance",
                "https://sochain.com/api/v2/get_address_balance/BTC/{}",
                "https://mempool.space/api/address/{}",
                "https://chain.api.btc.com/v3/address/{}"  # Новый endpoint
            ],
            "api_keys": [],
            "decimals": 8
        },
        "ETH": {
            "name": "Ethereum", 
            "api_urls": [
                "https://api.blockcypher.com/v1/eth/main/addrs/{}/balance",
                "https://api.etherscan.io/api?module=account&action=balance&address={}&tag=latest",
                "https://blockscout.com/eth/mainnet/api?module=account&action=balance&address={}",
                "https://api.ethplorer.io/getAddressInfo/{}?apiKey=freekey"  # Новый endpoint
            ],
            "api_keys": [],
            "decimals": 18
        },
        "USDT_ETH": {
            "name": "Tether (Ethereum)", 
            "api_urls": [
                "https://api.etherscan.io/api?module=account&action=tokenbalance&contractaddress=0xdac17f958d2ee523a2206206994597c13d831ec7&address={}",
                "https://api.blockcypher.com/v1/eth/main/addrs/{}/balance"
            ],
            "api_keys": [],
            "decimals": 6
        },
        "LTC": {
            "name": "Litecoin",
            "api_urls": [
                "https://api.blockcypher.com/v1/ltc/main/addrs/{}/balance",
                "https://sochain.com/api/v2/get_address_balance/LTC/{}"
            ],
            "api_keys": [],
            "decimals": 8
        },
        "XRP": {
            "name": "Ripple",
            "api_urls": [
                "https://api.xrpscan.com/api/v1/account/{}",
                "https://data.ripple.com/v2/accounts/{}/balances"
            ],
            "api_keys": [],
            "decimals": 6
        },
        "BCH": {
            "name": "Bitcoin Cash",
            "api_urls": [
                "https://api.blockchair.com/bitcoin-cash/dashboards/address/{}",
                "https://bch-chain.api.btc.com/v3/address/{}"
            ],
            "api_keys": [],
            "decimals": 8
        },
        "DOGE": {
            "name": "Dogecoin", 
            "api_urls": [
                "https://api.blockcypher.com/v1/doge/main/addrs/{}/balance",
                "https://sochain.com/api/v2/get_address_balance/DOGE/{}"
            ],
            "api_keys": [],
            "decimals": 8
        }
    }

    # Параметры проверки (оптимизированы для скорости)
    MIN_BALANCE = 0.0001
    MIN_TOTAL_BALANCE_USD = 1.0
    MIN_TX_COUNT = 1
    MIN_INACTIVE_DAYS = 90
    MAX_WORKERS = min(multiprocessing.cpu_count() * 2, 50)  # Уменьшено с 300 до 50
    BATCH_SIZE = 1000
    REQUEST_TIMEOUT = 15
    CACHE_EXPIRY = 3600
    ZERO_BALANCE_CACHE_EXPIRY = 86400  # 24 часа для нулевых балансов

    # Параметры двухэтапной проверки
    PRIMARY_CURRENCIES = ["BTC", "ETH", "LTC"]
    MIN_PRIMARY_BALANCE_USD = 0.1
    PRIMARY_CHECK_TIMEOUT = 5

    # Настройки путей
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    WORDLISTS_DIR = os.path.join(BASE_DIR, "bip39-wordlists")
    RESULTS_DIR = os.path.join(BASE_DIR, "found_wallets")
    CACHE_DIR = os.path.join(BASE_DIR, "cache")
    LOG_DIR = os.path.join(BASE_DIR, "logs")
    PATTERNS_DIR = os.path.join(BASE_DIR, "patterns")

    # Настройки для улучшенной генерации
    USE_HUMAN_PATTERNS = True
    USE_TX_ACTIVITY_CHECK = True
    USE_MULTIPLE_API_SOURCES = True
    USE_BATCH_API = True
    USE_PREFILTERING = True
    USE_PRIORITIZATION = True
    
    # Адаптивная фильтрация
    ADAPTIVE_FILTERING = True
    INITIAL_PREFILTER_THRESHOLD = 10
    MIN_PREFILTER_THRESHOLD = 5
    MAX_PREFILTER_THRESHOLD = 25
    FILTER_ADJUSTMENT_STEP = 2
    
    PREFILTER_THRESHOLD = INITIAL_PREFILTER_THRESHOLD

    # Кэширование и производительность
    USE_PERSISTENT_CACHE = True
    MAX_RETRIES = 5
    RETRY_DELAY = 0.5
    RETRY_BACKOFF = 2.0

    COMMON_PATTERNS_FILE = os.path.join(PATTERNS_DIR, "common_patterns.txt")
    MNEMONIC_PATTERNS_FILE = os.path.join(PATTERNS_DIR, "mnemonic_patterns.txt")
    KNOWN_PHRASES_FILE = os.path.join(PATTERNS_DIR, "known_phrases.txt")
    COMMON_PASSWORDS_FILE = os.path.join(PATTERNS_DIR, "common_passwords.txt")
    KEYBOARD_PATTERNS_FILE = os.path.join(PATTERNS_DIR, "keyboard_patterns.txt")
    CRYPTO_PATTERNS_FILE = os.path.join(PATTERNS_DIR, "crypto_patterns.txt")
    KNOWN_MNEMONICS_FILE = os.path.join(PATTERNS_DIR, "known_mnemonics.txt")
    CHECKED_MNEMONICS_FILE = os.path.join(BASE_DIR, "checked_mnemonics.txt")

    # Настройки базы данных известных кошельков
    KNOWN_WALLETS_DB = os.path.join(BASE_DIR, "known_wallets.db")
    DB_CACHE_SIZE = 20000
    DB_JOURNAL_MODE = "WAL"

    # Целевые криптовалюты для проверки
    TARGET_CURRENCIES = ["BTC", "ETH", "USDT_ETH", "LTC", "XRP", "BCH", "DOGE"]

    # Коэффициенты для эвристической оценки
    HEURISTIC_WEIGHTS = {
        'pattern_score': 0.5,
        'tx_activity': 0.2,
        'balance_score': 0.3,
        'mnemonic_quality': 0.4
    }

    # Настройки для длины мнемонической фразы и языков
    MNEMONIC_LENGTH = 12
    ENABLED_LANGUAGES = ['english']

    # Файл для сохранения настроек
    SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

    # Настройки API ключей
    API_KEYS_FILE = os.path.join(BASE_DIR, "api_keys.json")

    # Настройки логирования
    LOG_LEVEL = 'INFO'  # Изменено с DEBUG на INFO
    LOG_TO_FILE = True
    LOG_TO_CONSOLE = True  # Включен вывод в консоль
    LOG_FILE = os.path.join(LOG_DIR, "wallet_scanner.log")
    LOG_MAX_SIZE = 10 * 1024 * 1024
    LOG_BACKUP_COUNT = 5

    # Курсы валют по умолчанию (будут обновляться автоматически)
    exchange_rates = {
        'BTC': 112000,
        'ETH': 5000,
        'USDT': 1,
        'LTC': 150,
        'XRP': 0.5,
        'BCH': 400,
        'DOGE': 0.1
    }

    # Настройки для Selenium fallback
    USE_SELENIUM_FALLBACK = False
    SELENIUM_DRIVER_PATH = "/usr/local/bin/chromedriver"  # Путь к ChromeDriver

    # Настройки для OPCUA уведомлений
    USE_OPCUA_NOTIFICATIONS = False
    OPCUA_SERVER_URL = "opc.tcp://localhost:4840"
    OPCUA_NODE_ID = "ns=2;s=WalletFound"

    @classmethod
    def init_directories(cls):
        """Создание необходимых директорий"""
        for directory in [cls.RESULTS_DIR, cls.CACHE_DIR, cls.LOG_DIR, cls.WORDLISTS_DIR, cls.PATTERNS_DIR]:
            os.makedirs(directory, exist_ok=True)

        # Создаем файлы с общими паттернами, если их нет
        for file_path in [cls.COMMON_PATTERNS_FILE, cls.MNEMONIC_PATTERNS_FILE, cls.KNOWN_PHRASES_FILE, 
                         cls.COMMON_PASSWORDS_FILE, cls.KEYBOARD_PATTERNS_FILE, cls.CRYPTO_PATTERNS_FILE, 
                         cls.KNOWN_MNEMONICS_FILE, cls.CHECKED_MNEMONICS_FILE]:
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    if file_path == cls.COMMON_PASSWORDS_FILE:
                        f.write("password\n123456\nqwerty\nadmin\nletmein\nwelcome\nmonkey\n")
                    elif file_path == cls.KEYBOARD_PATTERNS_FILE:
                        f.write("qwerty\nasdfgh\nzxcvbn\n123456\n!@#$%^\n")
                    elif file_path == cls.COMMON_PATTERNS_FILE:
                        f.write("one two three four five six seven eight nine ten eleven twelve\n")
                        f.write("alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu\n")
                    elif file_path == cls.MNEMONIC_PATTERNS_FILE:
                        f.write("abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about\n")
                        f.write("legal winner thank year wave sausage worth useful legal winner thank yellow\n")
                        f.write("zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo wrong\n")
                        f.write("letter advice cage absurd amount doctor acoustic avoid letter advice cage above\n")
                        f.write("one two three four five six seven eight nine ten eleven twelve\n")
                        f.write("alpha beta gamma delta epsilon zeta eta theta iota kappa lambda\n")
                        f.write("bitcoin ethereum litecoin ripple bitcoin cash dogecoin tether monero\n")
                        f.write("crypto wallet private key seed phrase recovery passphrase\n")
                    elif file_path == cls.KNOWN_PHRASES_FILE:
                        f.write("abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about\n")
                    elif file_path == cls.CRYPTO_PATTERNS_FILE:
                        f.write("bitcoin ethereum wallet private key seed phrase\n")
                        f.write("crypto blockchain address transaction\n")
                    elif file_path == cls.KNOWN_MNEMONICS_FILE:
                        f.write("# Добавьте известные мнемонические фразы здесь, каждую на новой строке\n")
                    elif file_path == cls.CHECKED_MNEMONICS_FILE:
                        f.write("# Этот файл содержит хэши проверенных мнемонических фраз\n")

    @classmethod
    def load_settings(cls):
        """Загрузка настроек из файла"""
        try:
            if os.path.exists(cls.SETTINGS_FILE):
                with open(cls.SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    
                    # Обновляем настройки
                    for key, value in settings.items():
                        if hasattr(cls, key):
                            setattr(cls, key, value)
        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")

    @classmethod
    def load_api_keys(cls):
        """Загрузка API ключей из файла"""
        try:
            if os.path.exists(cls.API_KEYS_FILE):
                with open(cls.API_KEYS_FILE, 'r', encoding='utf-8') as f:
                    api_keys = json.load(f)
                    
                    # Обновляем API ключи
                    for currency, keys in api_keys.items():
                        if currency in cls.CRYPTOCURRENCIES:
                            cls.CRYPTOCURRENCIES[currency]["api_keys"] = keys
        except Exception as e:
            print(f"Ошибка загрузки API ключей: {e}")

    @classmethod
    def save_settings(cls):
        """Сохранение настроек в файл"""
        try:
            settings = {
                'MNEMONIC_LENGTH': cls.MNEMONIC_LENGTH,
                'ENABLED_LANGUAGES': cls.ENABLED_LANGUAGES,
                'MIN_TOTAL_BALANCE_USD': cls.MIN_TOTAL_BALANCE_USD,
                'MIN_TX_COUNT': cls.MIN_TX_COUNT,
                'MIN_INACTIVE_DAYS': cls.MIN_INACTIVE_DAYS,
                'MAX_WORKERS': cls.MAX_WORKERS,
                'BATCH_SIZE': cls.BATCH_SIZE,
                'REQUEST_TIMEOUT': cls.REQUEST_TIMEOUT,
                'USE_HUMAN_PATTERNS': cls.USE_HUMAN_PATTERNS,
                'USE_TX_ACTIVITY_CHECK': cls.USE_TX_ACTIVITY_CHECK,
                'USE_MULTIPLE_API_SOURCES': cls.USE_MULTIPLE_API_SOURCES,
                'USE_BATCH_API': cls.USE_BATCH_API,
                'USE_PREFILTERING': cls.USE_PREFILTERING,
                'USE_PRIORITIZATION': cls.USE_PRIORITIZATION,
                'ADAPTIVE_FILTERING': cls.ADAPTIVE_FILTERING,
                'INITIAL_PREFILTER_THRESHOLD': cls.INITIAL_PREFILTER_THRESHOLD,
                'MIN_PREFILTER_THRESHOLD': cls.MIN_PREFILTER_THRESHOLD,
                'MAX_PREFILTER_THRESHOLD': cls.MAX_PREFILTER_THRESHOLD,
                'FILTER_ADJUSTMENT_STEP': cls.FILTER_ADJUSTMENT_STEP,
                'PREFILTER_THRESHOLD': cls.PREFILTER_THRESHOLD,
                'TARGET_CURRENCIES': cls.TARGET_CURRENCIES,
                'PRIMARY_CURRENCIES': cls.PRIMARY_CURRENCIES,
                'MIN_PRIMARY_BALANCE_USD': cls.MIN_PRIMARY_BALANCE_USD,
                'PRIMARY_CHECK_TIMEOUT': cls.PRIMARY_CHECK_TIMEOUT,
                'USE_PERSISTENT_CACHE': cls.USE_PERSISTENT_CACHE,
                'MAX_RETRIES': cls.MAX_RETRIES,
                'RETRY_DELAY': cls.RETRY_DELAY,
                'RETRY_BACKOFF': cls.RETRY_BACKOFF,
                'ZERO_BALANCE_CACHE_EXPIRY': cls.ZERO_BALANCE_CACHE_EXPIRY,
                'LOG_LEVEL': cls.LOG_LEVEL,
                'LOG_TO_FILE': cls.LOG_TO_FILE,
                'LOG_TO_CONSOLE': cls.LOG_TO_CONSOLE,
                'USE_SELENIUM_FALLBACK': cls.USE_SELENIUM_FALLBACK,
                'SELENIUM_DRIVER_PATH': cls.SELENIUM_DRIVER_PATH,
                'USE_OPCUA_NOTIFICATIONS': cls.USE_OPCUA_NOTIFICATIONS,
                'OPCUA_SERVER_URL': cls.OPCUA_SERVER_URL,
                'OPCUA_NODE_ID': cls.OPCUA_NODE_ID
            }
            
            with open(cls.SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")

# Инициализация директорий
Config.init_directories()

# Загрузка настроек при импорте модуля
Config.load_settings()
Config.load_api_keys()

# Создаем экземпляр конфигурации для обратной совместимости
config = Config()

"""
Менеджер для управления асинхронными операциями и циклом событий.
"""
import threading

class AsyncManager:
    """Класс для управления асинхронными операциями"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AsyncManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.loop = None
        self._running = False
        self._thread = None
        self._tasks = set()
        self._initialized = True
    
    def start(self):
        """Запуск цикла событий в отдельном потоке"""
        if self._running:
            return
            
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        
        # Ждем инициализации цикла
        while self.loop is None:
            time.sleep(0.1)
    
    def stop(self):
        """Остановка цикла событий"""
        if not self._running:
            return
            
        self._running = False
        if self.loop and self.loop.is_running():
            # Отменяем все задачи
            for task in self._tasks:
                if not task.done():
                    task.cancel()
            
            # Останавливаем цикл
            self.loop.call_soon_threadsafe(self.loop.stop)
        
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None
    
    def _run_loop(self):
        """Запуск цикла событий"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_forever()
        finally:
            # Завершаем все оставшиеся задачи
            pending = asyncio.all_tasks(self.loop)
            for task in pending:
                task.cancel()
            
            # Дожидаемся завершения задач
            if pending:
                self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            
            self.loop.close()
            self.loop = None
    
    def run_async(self, coro):
        """Запуск корутины в цикле событий"""
        if not self._running or not self.loop:
            raise RuntimeError("AsyncManager не запущен")
        
        # Создаем задачу и добавляем ее в набор
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        task = future._task
        self._tasks.add(task)
        
        # Удаляем задачу после завершения
        task.add_done_callback(lambda t: self._tasks.discard(t))
        
        return future

# Глобальный экземпляр менеджера
async_manager = AsyncManager()

def async_command(func):
    """Декоратор для асинхронных команд"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        return async_manager.run_async(func(*args, **kwargs))
    return wrapper

# Глобальный кэш для результатов запросов
request_cache = {}
exchange_rates = {}  # Для хранения курсов валют

# Загрузка постоянного кэша
if Config.USE_PERSISTENT_CACHE:
    try:
        cache_file = f"{Config.CACHE_DIR}/api_cache.json"
        with open(cache_file, 'r', encoding='utf-8') as f:
            request_cache = json.load(f)
    except:
        request_cache = {}

async def make_async_request(session, url, retry_count=0):
    """Асинхронное выполнение HTTP запроса с повторными попытками"""
    if retry_count >= Config.MAX_RETRIES:
        return None
        
    try:
        async with session.get(url, timeout=Config.REQUEST_TIMEOUT) as response:
            if response.status == 200:
                return await response.text()
            elif response.status == 429:  # Too Many Requests
                await asyncio.sleep(Config.RETRY_DELAY * (2 ** retry_count))
                return await make_async_request(session, url, retry_count + 1)
            else:
                return None
    except (aiohttp.ClientError, asyncio.TimeoutError):
        await asyncio.sleep(Config.RETRY_DELAY * (2 ** retry_count))
        return await make_async_request(session, url, retry_count + 1)
    except Exception as e:
        return None

async def make_batch_request(session, urls):
    """Выполнение пакетных HTTP запросов"""
    tasks = [make_async_request(session, url) for url in urls]
    return await asyncio.gather(*tasks)

async def get_balances_batch_async(session, currency_address_pairs):
    """Пакетное получение балансов для нескольких валют и адресов"""
    cache_keys = []
    current_time = time.time()
    results = {}
    
    # Проверяем кэш
    for currency, address in currency_address_pairs:
        cache_key = f"{currency}_{address}"
        cache_keys.append(cache_key)
        
        if cache_key in request_cache:
            cached_time, balance = request_cache[cache_key]
            # Для нулевых балансов используем более длительное кэширование
            cache_expiry = Config.ZERO_BALANCE_CACHE_EXPIRY if balance == 0 else Config.CACHE_EXPIRY
            if current_time - cached_time < cache_expiry:
                results[cache_key] = balance
                continue
    
    # Формируем URL для запросов, которые не в кэше
    urls_to_fetch = []
    keys_to_fetch = []
    
    for currency, address in currency_address_pairs:
        cache_key = f"{currency}_{address}"
        if cache_key not in results:
            if currency in Config.CRYPTOCURRENCIES:
                # Используем первый доступный API URL
                api_url = Config.CRYPTOCURRENCIES[currency]["api_urls"][0]
                url = api_url.format(address)
                urls_to_fetch.append(url)
                keys_to_fetch.append(cache_key)
    
    # Выполняем пакетные запросы
    if urls_to_fetch:
        responses = await make_batch_request(session, urls_to_fetch)
        
        for i, response in enumerate(responses):
            cache_key = keys_to_fetch[i]
            currency = cache_key.split("_")[0]
            balance = 0
            
            if response:
                try:
                    # Используем decimals из конфига вместо жестко заданных значений
                    decimals = Config.CRYPTOCURRENCIES[currency]["decimals"]
                    
                    if currency == "BTC":
                        balance = int(response) / (10 ** decimals)
                    elif currency == "LTC":
                        data = json.loads(response)
                        balance = data.get('balance', 0) / (10 ** decimals)
                    elif currency == "XRP":
                        data = json.loads(response)
                        balance = float(data.get('xrp_balance', 0))
                    elif currency == "BCH":
                        data = json.loads(response)
                        balance = float(data.get('balance', 0)) / (10 ** decimals)
                    elif currency == "DOGE":
                        data = json.loads(response)
                        balance = data.get('balance', 0) / (10 ** decimals)
                    elif currency in ["ETH", "USDT_ETH"]:
                        data = json.loads(response)
                        balance = int(data.get('result', 0)) / (10 ** decimals) if data.get('status') == '1' else 0
                except Exception as e:
                    print(f"Ошибка обработки ответа для {currency}: {e}")
                    balance = 0
            
            results[cache_key] = balance
            request_cache[cache_key] = (current_time, balance)
    
    return results

async def get_primary_balances_batch(session, addresses_data):
    """Пакетная проверка балансов для первичных валют"""
    results = {}
    currency_address_pairs = []
    
    for data in addresses_data:
        currency, address = data['currency'], data['address']
        cache_key = f"{currency}_{address}"
        
        # Проверяем кэш
        if cache_key in request_cache:
            cached_time, balance = request_cache[cache_key]
            # Для нулевых балансов используем более длительное кэширование
            cache_expiry = Config.ZERO_BALANCE_CACHE_EXPIRY if balance == 0 else Config.CACHE_EXPIRY
            if time.time() - cached_time < cache_expiry:
                results[cache_key] = balance
                continue
        
        currency_address_pairs.append((currency, address))
    
    # Пакетная проверка оставшихся адресов
    if currency_address_pairs:
        balance_results = await get_balances_batch_async(session, currency_address_pairs)
        results.update(balance_results)
    
    return results

async def get_exchange_rates(session):
    """Получение актуальных курсов криптовалют к USD"""
    global exchange_rates
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,tether,litecoin,ripple,bitcoin-cash,dogecoin&vs_currencies=usd"
        async with session.get(url, timeout=10) as response:
            if response.status == 200:
                data = await response.json()
                exchange_rates = {
                    'BTC': data.get('bitcoin', {}).get('usd', 0),
                    'ETH': data.get('ethereum', {}).get('usd', 0),
                    'USDT': data.get('tether', {}).get('usd', 1),
                    'LTC': data.get('litecoin', {}).get('usd', 0),
                    'XRP': data.get('ripple', {}).get('usd', 0),
                    'BCH': data.get('bitcoin-cash', {}).get('usd', 0),
                    'DOGE': data.get('dogecoin', {}).get('usd', 0)
                }
    except Exception as e:
        print(f"Ошибка получения курсов валют: {e}")
        # Используем Selenium как fallback
        await get_exchange_rates_selenium_fallback()
    
    # Если все еще не удалось получить курсы, используем значения по умолчанию
    if not exchange_rates:
        exchange_rates = {
            'BTC': 50000,
            'ETH': 3000,
            'USDT': 1,
            'LTC': 150,
            'XRP': 0.5,
            'BCH': 400,
            'DOGE': 0.1
        }

async def get_exchange_rates_selenium_fallback():
    """Получение курсов валют с помощью Selenium (fallback)"""
    global exchange_rates
    if not Config.USE_SELENIUM_FALLBACK:
        return
    
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=options)
        driver.get("https://www.coingecko.com/")
        
        # Ждем загрузки данных
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "coin-table"))
        )
        
        # Извлекаем данные о курсах
        rates = {}
        rows = driver.find_elements(By.CSS_SELECTOR, "tr[data-coin-symbol]")
        for row in rows:
            symbol = row.get_attribute("data-coin-symbol").upper()
            price_element = row.find_element(By.CSS_SELECTOR, "td[data-price]")
            price = float(price_element.get_attribute("data-price"))
            rates[symbol] = price
        
        driver.quit()
        exchange_rates = rates
    except Exception as e:
        print(f"Ошибка получения курсов через Selenium: {e}")

async def get_balance_async(session, currency, address):
    """Асинхронное получение баланса для конкретной валюты"""
    cache_key = f"{currency}_{address}"
    current_time = time.time()
    
    # Проверяем кэш
    if cache_key in request_cache:
        cached_time, balance = request_cache[cache_key]
        # Для нулевых балансов используем более длительное кэширование
        cache_expiry = Config.ZERO_BALANCE_CACHE_EXPIRY if balance == 0 else Config.CACHE_EXPIRY
        if current_time - cached_time < cache_expiry:
            return balance
    
    try:
        balance = 0
        
        # Перебираем все доступные API URL для данной валюты
        for api_url in Config.CRYPTOCURRENCIES[currency]["api_urls"]:
            try:
                response = await make_async_request(session, api_url.format(address))
                if not response:
                    continue
                    
                # Используем decimals из конфига вместо жестко заданных значений
                decimals = Config.CRYPTOCURRENCIES[currency]["decimals"]
                
                if currency == "BTC":
                    if "blockchain.info" in api_url:
                        balance = int(response) / (10 ** decimals)
                    elif "blockcypher.com" in api_url:
                        data = json.loads(response)
                        balance = data.get('balance', 0) / (10 ** decimals)
                    elif "sochain.com" in api_url:
                        data = json.loads(response)
                        balance = float(data.get('data', {}).get('confirmed_balance', 0))
                    elif "mempool.space" in api_url:
                        data = json.loads(response)
                        balance = data.get('chain_stats', {}).get('funded_txo_sum', 0) - data.get('chain_stats', {}).get('spent_txo_sum', 0)
                        balance = balance / (10 ** decimals)
                    break
                    
                elif currency == "LTC":
                    if "blockcypher.com" in api_url:
                        data = json.loads(response)
                        balance = data.get('balance', 0) / (10 ** decimals)
                    elif "sochain.com" in api_url:
                        data = json.loads(response)
                        balance = float(data.get('data', {}).get('confirmed_balance', 0))
                    break
                    
                elif currency == "XRP":
                    if "xrpscan.com" in api_url:
                        data = json.loads(response)
                        balance = float(data.get('xrp_balance', 0))
                    elif "ripple.com" in api_url:
                        data = json.loads(response)
                        balances = data.get('balances', [])
                        if balances:
                            balance = float(balances[0].get('value', 0))
                    break
                    
                elif currency == "BCH":
                    if "blockchair.com" in api_url:
                        data = json.loads(response)
                        address_data = data.get('data', {}).get(address, {})
                        balance = address_data.get('address', {}).get('balance', 0) / (10 ** decimals)
                    elif "btc.com" in api_url:
                        data = json.loads(response)
                        balance = float(data.get('data', {}).get('balance', 0)) / (10 ** decimals)
                    break
                    
                elif currency == "DOGE":
                    if "blockcypher.com" in api_url:
                        data = json.loads(response)
                        balance = data.get('balance', 0) / (10 ** decimals)
                    elif "sochain.com" in api_url:
                        data = json.loads(response)
                        balance = float(data.get('data', {}).get('confirmed_balance', 0))
                    break
                    
                elif currency in ["ETH", "USDT_ETH"]:
                    if "etherscan.io" in api_url:
                        data = json.loads(response)
                        balance = int(data.get('result', 0)) / (10 ** decimals) if data.get('status') == '1' else 0
                    elif "blockcypher.com" in api_url:
                        data = json.loads(response)
                        balance = data.get('balance', 0) / (10 ** decimals)
                    break
                    
            except Exception as e:
                print(f"Ошибка обработки API ответа для {currency}: {e}")
                continue
                
        request_cache[cache_key] = (current_time, balance)
        return balance
    except Exception as e:
        print(f"Ошибка получения баланса для {currency}: {e}")
        return 0

async def get_transaction_count(session, currency, address):
    """Получение количества транзакций для адреса"""
    cache_key = f"{currency}_tx_{address}"
    current_time = time.time()
    
    if cache_key in request_cache:
        cached_time, tx_count = request_cache[cache_key]
        if current_time - cached_time < Config.CACHE_EXPIRY:
            return tx_count
    
    try:
        tx_count = 0
        
        if currency == "BTC":
            url = f"https://blockchain.info/rawaddr/{address}?limit=0"
            response = await make_async_request(session, url)
            if response:
                data = json.loads(response)
                tx_count = data.get('n_tx', 0)
        
        elif currency == "ETH":
            url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&page=1&offset=1&sort=asc"
            response = await make_async_request(session, url)
            if response:
                data = json.loads(response)
                tx_count = len(data.get('result', [])) if data.get('status') == '1' else 0
            
        request_cache[cache_key] = (current_time, tx_count)
        return tx_count
    except Exception as e:
        print(f"Ошибка получения количества транзакций для {currency}: {e}")
        return 0

@async_command
async def check_balances_batch_async(addresses):
    """Асинхронная пакетная проверка балансов для всех криптовалют"""
    balances = {}
    usd_balances = {}
    total_usd = 0
    tx_activity = {}
    
    async with aiohttp.ClientSession() as session:
        # Получаем актуальные курсы
        await get_exchange_rates(session)
        
        # Формируем пары валют и адресов для пакетной обработки
        currency_address_pairs = []
        for currency in Config.TARGET_CURRENCIES:
            if currency in ["ETH", "USDT_ETH"]:
                address = addresses["eth"]
            else:
                address = addresses["btc"]
            
            currency_address_pairs.append((currency, address))
        
        # Используем пакетную обработку, если включена
        if Config.USE_BATCH_API:
            balance_results_dict = await get_balances_batch_async(session, currency_address_pairs)
            
            # Преобразуем результаты в формат, совместимый с остальным кодом
            for currency in Config.TARGET_CURRENCIES:
                if currency in ["ETH", "USDT_ETH"]:
                    address = addresses["eth"]
                else:
                    address = addresses["btc"]
                
                cache_key = f"{currency}_{address}"
                balances[currency] = balance_results_dict.get(cache_key, 0)
        else:
            # Старый метод для обратной совместимости
            balance_tasks = []
            for currency in Config.TARGET_CURRENCIES:
                if currency in ["ETH", "USDT_ETH"]:
                    address = addresses["eth"]
                else:
                    address = addresses["btc"]
                
                balance_tasks.append(get_balance_async(session, currency, address))
            
            # Выполняем все задачи параллельно
            balance_results = await asyncio.gather(*balance_tasks)
            
            for i, currency in enumerate(Config.TARGET_CURRENCIES):
                balances[currency] = balance_results[i]
        
        # Создаем задачи для транзакций (если включена проверка активности)
        tx_tasks = []
        if Config.USE_TX_ACTIVITY_CHECK:
            for currency in Config.TARGET_CURRENCIES:
                if currency in ["BTC", "ETH"]:
                    if currency in ["ETH", "USDT_ETH"]:
                        address = addresses["eth"]
                    else:
                        address = addresses["btc"]
                    
                    tx_tasks.append(get_transaction_count(session, currency, address))
        
        # Выполняем задачи для транзакций параллельно
        tx_results = await asyncio.gather(*tx_tasks) if tx_tasks else []
        
        # Обрабатываем результаты балансов
        for i, currency in enumerate(Config.TARGET_CURRENCIES):
            # Определяем курс для конвертации
            rate = 0
            if "USDT" in currency:
                rate = exchange_rates.get('USDT', 1)
            else:
                rate = exchange_rates.get(currency, 0)
            
            # Конвертируем в USD
            usd_value = balances[currency] * rate
            usd_balances[currency] = usd_value
            total_usd += usd_value
        
        # Обрабатываем результаты транзакций
        if Config.USE_TX_ACTIVITY_CHECK:
            tx_index = 0
            for currency in Config.TARGET_CURRENCIES:
                if currency in ["BTC", "ETH"]:
                    tx_activity[currency] = tx_results[tx_index] if tx_index < len(tx_results) else 0
                    tx_index += 1
    
    return {
        'crypto_balances': balances,
        'usd_balances': usd_balances,
        'total_usd': total_usd,
        'tx_activity': tx_activity
    }

# Сохранение кэша при выходе
import atexit
def save_api_cache():
    if Config.USE_PERSISTENT_CACHE:
        try:
            cache_file = f"{Config.CACHE_DIR}/api_cache.json"
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(request_cache, f, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения кэша API: {e}")

atexit.register(save_api_cache)

"""
Криптографический модуль с оптимизированными функции.
Использует кэширование и предварительные вычисления для ускорения работы.
"""
import hashlib
import ecdsa
import base58
from Crypto.Hash import RIPEMD160

# Кэш для предварительно вычисленных ключей
_key_cache = {}
_CACHE_SIZE = 20000

# Кэш для известных мнемонических фраз
_known_mnemonics_set = set()

# Кэш для проверенных мнемонических фраз
_checked_mnemonics_set = set()

# Кэш для паттернов
_patterns_cache = None

def save_key_cache():
    """Сохранение кэша ключей на диск"""
    if not Config.USE_PERSISTENT_CACHE:
        return
    
    cache_file = os.path.join(Config.CACHE_DIR, "key_cache.json")
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(_key_cache, f, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения кэша ключей: {e}")

def load_key_cache():
    """Загрузка кэша ключей с диска"""
    global _key_cache
    if not Config.USE_PERSISTENT_CACHE:
        return
    
    cache_file = os.path.join(Config.CACHE_DIR, "key_cache.json")
    try:
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                _key_cache = json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки кэша ключей: {e}")
        _key_cache = {}

def load_known_mnemonics():
    """Загрузка известных мнемонических фраз"""
    global _known_mnemonics_set
    try:
        if os.path.exists(Config.KNOWN_MNEMONICS_FILE):
            # Попробуем разные кодировки
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            for encoding in encodings:
                try:
                    with open(Config.KNOWN_MNEMONICS_FILE, 'r', encoding=encoding) as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                _known_mnemonics_set.add(line)
                    logger.info(f"Загружено {len(_known_mnemonics_set)} известных мнемонических фраз")
                    break
                except UnicodeDecodeError:
                    continue
    except Exception as e:
        logger.error(f"Ошибка загрузки известных мнемонических фраз: {e}")

def load_checked_mnemonics():
    """Загрузка проверенных мнемонических фраз"""
    global _checked_mnemonics_set
    try:
        if os.path.exists(Config.CHECKED_MNEMONICS_FILE):
            # Попробуем разные кодировки
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            for encoding in encodings:
                try:
                    with open(Config.CHECKED_MNEMONICS_FILE, 'r', encoding=encoding) as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                _checked_mnemonics_set.add(line)
                    logger.info(f"Загружено {len(_checked_mnemonics_set)} проверенных мнемонических фраз")
                    break
                except UnicodeDecodeError:
                    continue
    except Exception as e:
        logger.error(f"Ошибка загрузки проверенных мнемонических фраз: {e}")

def save_checked_mnemonics():
    """Сохранение проверенных мнемонических фраз"""
    try:
        with open(Config.CHECKED_MNEMONICS_FILE, 'w', encoding='utf-8') as f:
            for mnemonic in _checked_mnemonics_set:
                f.write(f"{mnemonic}\n")
        logger.info(f"Сохранено {len(_checked_mnemonics_set)} проверенных мнемонических фраз")
    except Exception as e:
        logger.error(f"Ошибка сохранения проверенных мнемонических фраз: {e}")

def add_checked_mnemonic(mnemonic):
    """Добавление мнемонической фразы в список проверенных"""
    # Сохраняем хэш мнемонической фразы для конфиденциальности
    mnemonic_hash = hashlib.sha256(mnemonic.encode('utf-8')).hexdigest()
    _checked_mnemonics_set.add(mnemonic_hash)
    
    # Периодически сохраняем на диск (например, каждые 100 добавлений)
    if len(_checked_mnemonics_set) % 100 == 0:
        save_checked_mnemonics()

def is_mnemonic_checked(mnemonic):
    """Проверка, была ли уже проверена мнемоническая фраза"""
    mnemonic_hash = hashlib.sha256(mnemonic.encode('utf-8')).hexdigest()
    return mnemonic_hash in _checked_mnemonics_set

def get_common_patterns():
    """Кэшированная загрузка паттернов"""
    global _patterns_cache
    if _patterns_cache is None:
        _patterns_cache = load_common_patterns()
    return _patterns_cache

# Загружаем кэш при импорте модуля
load_key_cache()
load_known_mnemonics()
load_checked_mnemonics()

def generate_entropy(strength=128):
    """Генерация криптографически безопасной энтропии"""
    return os.urandom(strength // 8)

def entropy_to_mnemonic(entropy, wordlist):
    """Преобразование энтропии в мнемоническую фразу"""
    if len(entropy) not in [16, 20, 24, 28, 32]:
        raise ValueError("Длина энтропии должна быть 16, 20, 24, 28 или 32 байта")
    
    entropy_hash = hashlib.sha256(entropy).digest()
    checksum_bits = bin(int.from_bytes(entropy_hash, 'big'))[2:].zfill(256)[:len(entropy) * 8 // 32]
    
    entropy_bits = bin(int.from_bytes(entropy, 'big'))[2:].zfill(len(entropy) * 8)
    combined_bits = entropy_bits + checksum_bits
    
    indices = []
    for i in range(0, len(combined_bits), 11):
        index = int(combined_bits[i:i+11], 2)
        indices.append(index)
    
    return ' '.join([wordlist[i] for i in indices])

def mnemonic_to_seed(mnemonic, passphrase=""):
    """Преобразование мнемонической фразы в seed"""
    salt = f"mnemonic{passphrase}".encode('utf-8')
    return hashlib.pbkdf2_hmac('sha512', mnemonic.encode('utf-8'), salt, 2048, 64)

def derive_eth_address(seed):
    """Получение Ethereum адреса из seed"""
    private_key = ecdsa.SigningKey.from_string(seed[:32], curve=ecdsa.SECP256k1)
    public_key = private_key.get_verifying_key().to_string()
    keccak_hash = hashlib.sha3_256(public_key).digest()
    return '0x' + keccak_hash[-20:].hex()

def derive_btc_address(seed):
    """Получение Bitcoin адреса из seed"""
    private_key = ecdsa.SigningKey.from_string(seed[:32], curve=ecdsa.SECP256k1)
    public_key = private_key.get_verifying_key().to_string()
    sha256_hash = hashlib.sha256(public_key).digest()
    ripemd160_hash = RIPEMD160.new(sha256_hash).digest()
    network_byte = b'\x00'
    payload = network_byte + ripemd160_hash
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    address_bytes = payload + checksum
    return base58.b58encode(address_bytes).decode('ascii')

def derive_ltc_address(seed):
    """Получение Litecoin адреса из seed"""
    private_key = ecdsa.SigningKey.from_string(seed[:32], curve=ecdsa.SECP256k1)
    public_key = private_key.get_verifying_key().to_string()
    sha256_hash = hashlib.sha256(public_key).digest()
    ripemd160_hash = RIPEMD160.new(sha256_hash).digest()
    network_byte = b'\x30'  # Префикс для Litecoin mainnet
    payload = network_byte + ripemd160_hash
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    address_bytes = payload + checksum
    return base58.b58encode(address_bytes).decode('ascii')

def derive_bch_address(seed):
    """Получение Bitcoin Cash адреса из seed"""
    # Bitcoin Cash использует cashaddr format, но для совместимости с API используем legacy format
    private_key = ecdsa.SigningKey.from_string(seed[:32], curve=ecdsa.SECP256k1)
    public_key = private_key.get_verifying_key().to_string()
    sha256_hash = hashlib.sha256(public_key).digest()
    ripemd160_hash = RIPEMD160.new(sha256_hash).digest()
    network_byte = b'\x00'  # Префикс для Bitcoin Cash legacy address
    payload = network_byte + ripemd160_hash
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    address_bytes = payload + checksum
    return base58.b58encode(address_bytes).decode('ascii')

def derive_xrp_address(seed):
    """Получение Ripple адреса из seed"""
    # XRP использует другой алгоритм для генерации адресов
    # Для упрощения используем тот же подход, что и для BTC, но с другим префиксом
    private_key = ecdsa.SigningKey.from_string(seed[:32], curve=ecdsa.SECP256k1)
    public_key = private_key.get_verifying_key().to_string()
    sha256_hash = hashlib.sha256(public_key).digest()
    ripemd160_hash = RIPEMD160.new(sha256_hash).digest()
    # XRP использует base58 с другим алфавитом, но для простоты используем стандартный base58
    return "r" + base58.b58encode(ripemd160_hash).decode('ascii')[:33]

def derive_doge_address(seed):
    """Получение Dogecoin адреса из seed"""
    private_key = ecdsa.SigningKey.from_string(seed[:32], curve=ecdsa.SECP256k1)
    public_key = private_key.get_verifying_key().to_string()
    sha256_hash = hashlib.sha256(public_key).digest()
    ripemd160_hash = RIPEMD160.new(sha256_hash).digest()
    network_byte = b'\x1e'  # Префикс для Dogecoin mainnet
    payload = network_byte + ripemd160_hash
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    address_bytes = payload + checksum
    return base58.b58encode(address_bytes).decode('ascii')

@lru_cache(maxsize=_CACHE_SIZE)
def cached_mnemonic_to_seed(mnemonic, passphrase=""):
    """Кэшированная версия mnemonic_to_seed"""
    return mnemonic_to_seed(mnemonic, passphrase)

@lru_cache(maxsize=_CACHE_SIZE)
def cached_derive_eth_address(seed):
    """Кэшированная версия derive_eth_address"""
    return derive_eth_address(seed)

@lru_cache(maxsize=_CACHE_SIZE)
def cached_derive_btc_address(seed):
    """Кэшированная версия derive_btc_address"""
    return derive_btc_address(seed)

@lru_cache(maxsize=_CACHE_SIZE)
def cached_derive_ltc_address(seed):
    """Кэшированная версия derive_ltc_address"""
    return derive_ltc_address(seed)

@lru_cache(maxsize=_CACHE_SIZE)
def cached_derive_bch_address(seed):
    """Кэшированная версия derive_bch_address"""
    return derive_bch_address(seed)

@lru_cache(maxsize=_CACHE_SIZE)
def cached_derive_xrp_address(seed):
    """Кэшированная версия derive_xrp_address"""
    return derive_xrp_address(seed)

@lru_cache(maxsize=_CACHE_SIZE)
def cached_derive_doge_address(seed):
    """Кэшированная версия derive_doge_address"""
    return derive_doge_address(seed)

def load_common_patterns():
    """Загрузка распространенных паттернов из файлов"""
    patterns = []
    
    # Загрузка mnemonic_patterns.txt (основной источник мнемонических паттернов)
    try:
        if os.path.exists(Config.MNEMONIC_PATTERNS_FILE):
            with open(Config.MNEMONIC_PATTERNS_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Проверяем, что паттерн состоит из слов BIP-39
                        words = line.split()
                        if all(word in _get_combined_wordlist() for word in words):
                            patterns.append(line)
            logger.info(f"Загружено {len(patterns)} мнемонических паттернов из {Config.MNEMONIC_PATTERNS_FILE}")
    except Exception as e:
        logger.error(f"Ошибка загрузки {Config.MNEMONIC_PATTERNS_FILE}: {e}")
    
    # Загрузка common_passwords.txt (вторичный источник)
    try:
        if os.path.exists(Config.COMMON_PASSWORDS_FILE):
            with open(Config.COMMON_PASSWORDS_FILE, 'r', encoding='utf-8') as f:
                passwords = [line.strip() for line in f if line.strip()]
                # Фильтруем пароли, оставляя только те, которые состоят из BIP-39 слов
                for password in passwords:
                    words = password.split()
                    if len(words) >= 3 and all(word in _get_combined_wordlist() for word in words):
                        patterns.append(password)
            logger.info(f"Загружено {len(patterns)} паттернов из {Config.COMMON_PASSWORDS_FILE}")
    except Exception as e:
        logger.error(f"Ошибка загрузки {Config.COMMON_PASSWORDS_FILE}: {e}")
    
    # Загрузка known_phrases.txt
    try:
        if os.path.exists(Config.KNOWN_PHRASES_FILE):
            with open(Config.KNOWN_PHRASES_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        patterns.append(line)
            logger.info(f"Загружено {len(patterns)} паттернов из {Config.KNOWN_PHRASES_FILE}")
    except Exception as e:
        logger.error(f"Ошибка загрузки {Config.KNOWN_PHRASES_FILE}: {e}")
    
    # Загрузка common_patterns.txt
    try:
        if os.path.exists(Config.COMMON_PATTERNS_FILE):
            with open(Config.COMMON_PATTERNS_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        patterns.append(line)
            logger.info(f"Загружено {len(patterns)} паттернов из {Config.COMMON_PATTERNS_FILE}")
    except Exception as e:
        logger.error(f"Ошибка загрузки {Config.COMMON_PATTERNS_FILE}: {e}")
    
    # Загрузка keyboard_patterns.txt
    try:
        if os.path.exists(Config.KEYBOARD_PATTERNS_FILE):
            with open(Config.KEYBOARD_PATTERNS_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        patterns.append(line)
            logger.info(f"Загружено {len(patterns)} паттернов из {Config.KEYBOARD_PATTERNS_FILE}")
    except Exception as e:
        logger.error(f"Ошибка загрузки {Config.KEYBOARD_PATTERNS_FILE}: {e}")
    
    # Загрузка crypto_patterns.txt
    try:
        if os.path.exists(Config.CRYPTO_PATTERNS_FILE):
            with open(Config.CRYPTO_PATTERNS_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        patterns.append(line)
            logger.info(f"Загружено {len(patterns)} паттернов из {Config.CRYPTO_PATTERNS_FILE}")
    except Exception as e:
        logger.error(f"Ошибка загрузки {Config.CRYPTO_PATTERNS_FILE}: {e}")
    
    return patterns

def _get_combined_wordlist():
    """Получение объединенного словаря всех языков BIP-39"""
    combined = set()
    for lang in Config.ENABLED_LANGUAGES:
        wordlist_file = os.path.join(Config.WORDLISTS_DIR, f"{lang}.txt")
        if os.path.exists(wordlist_file):
            with open(wordlist_file, 'r', encoding='utf-8') as f:
                combined.update(line.strip() for line in f)
    return combined

def generate_human_mnemonic(wordlist, length=12, pattern_type=None):
    """Генерация мнемонических фраз BIP-39 с уникальными словами"""
    # Всегда гарантируем уникальность слов
    if not Config.USE_HUMAN_PATTERNS:
        # Случайная генерация без повторений (правильная BIP-39)
        mnemonic = ' '.join(random.sample(wordlist, length))
        logger.debug(f"Сгенерирована случайная мнемоническая фраза: {mnemonic}")
        return mnemonic
    
    common_patterns = get_common_patterns()
    
    if common_patterns and random.random() < 0.7:
        pattern = random.choice(common_patterns)
        words = pattern.split()
        
        # Фильтруем слова, оставляя только те, что есть в словаре BIP-39
        valid_words = [word for word in words if word in wordlist]
        
        # Удаляем дубликаты
        unique_words = []
        seen = set()
        for word in valid_words:
            if word not in seen:
                seen.add(word)
                unique_words.append(word)
        
        # Обрезаем или дополняем до нужной длины
        if len(unique_words) > length:
            unique_words = unique_words[:length]
        else:
            # Дополняем случайными уникальными словами из BIP-39
            remaining_words = [w for w in wordlist if w not in seen]
            needed = min(length - len(unique_words), len(remaining_words))
            if needed > 0:
                additional = random.sample(remaining_words, needed)
                unique_words.extend(additional)
        
        mnemonic = ' '.join(unique_words)
        logger.debug(f"Сгенерирована мнемоническая фраза на основе паттерна: {mnemonic}")
        return mnemonic
    
    # Случайная генерация без повторений (правильная BIP-39)
    mnemonic = ' '.join(random.sample(wordlist, length))
    logger.debug(f"Сгенерирована случайная мнемоническая фраза: {mnemonic}")
    return mnemonic

def enhanced_heuristic_score(address, mnemonic=None):
    """Улучшенная эвристическая оценка с учетом мнемонической фразы"""
    score = 0
    
    # Базовые проверки адреса
    if address.startswith('0x'):
        # Для ETH адресов
        hex_part = address[2:]
        
        # Проверка на наличие последовательностей
        sequences = ['123', 'abc', '000', '111', '222', '333', '444', '555', '666', '777', '888', '999']
        for seq in sequences:
            if seq in hex_part:
                score += 20
        
        # Проверка на повторяющиеся символы
        for i in range(len(hex_part) - 3):
            if hex_part[i] == hex_part[i+1] == hex_part[i+2]:
                score += 15
        
        # Проверка на короткие адреса (vanity addresses)
        if len(set(hex_part)) < 8:
            score += 25
            
        # Проверка на паттерны, характерные для кошельков с балансом
        if hex_part.startswith('dead') or hex_part.endswith('beef'):
            score += 30
            
        # Проверка на повторяющиеся символы в начале
        if len(hex_part) >= 4 and hex_part[0] == hex_part[1] == hex_part[2] == hex_part[3]:
            score += 20
            
        # Проверка на повторяющиеся символы в конце
        if len(hex_part) >= 4 and hex_part[-1] == hex_part[-2] == hex_part[-3] == hex_part[-4]:
            score += 20
    
    # Анализ мнемонической фразы
    if mnemonic:
        words = mnemonic.split()
        
        # Проверка на повторяющиеся слова
        if len(words) != len(set(words)):
            score -= 50  # Штраф за повторяющиеся слова
        
        # Проверка на наличие common patterns
        common_patterns = get_common_patterns()
        for pattern in common_patterns:
            if pattern in mnemonic:
                score += 25
                break
                
        # Проверка на известные мнемонические фразы
        if mnemonic in _known_mnemonics_set:
            score += 100
    
    logger.debug(f"Эвристическая оценка для адреса {address}: {score}")
    return max(0, score)

def assess_mnemonic_quality(mnemonic):
    """Оценка качества мнемонической фразы"""
    score = 0
    words = mnemonic.split()
    
    # Проверка на уникальность слов
    if len(words) == len(set(words)):
        score += 30
    
    # Проверка на наличие common patterns
    common_patterns = get_common_patterns()
    for pattern in common_patterns:
        if pattern in mnemonic:
            score += 25
            break
    
    # Проверка на длину слов (более длинные слова часто реже используются)
    avg_word_length = sum(len(word) for word in words) / len(words)
    if avg_word_length > 6:
        score += 15
    
    # Проверка на известные мнемонические фразы
    if mnemonic in _known_mnemonics_set:
        score += 100
    
    logger.debug(f"Оценка качества мнемонической фразы {mnemonic[:20]}...: {score}")
    return score

# Сохраняем кэш при выходе
atexit.register(save_checked_mnemonics)
atexit.register(save_key_cache)

"""
Модуль для работы с базой данных известных кошельков.
"""
import sqlite3

class KnownWalletsDB:
    """База данных известных кошельков"""
    
    def __init__(self, db_path=Config.KNOWN_WALLETS_DB):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Оптимизированная инициализация базы данных"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Включаем журналирование WAL для лучшей производительности
        c.execute("PRAGMA journal_mode=WAL")
        
        # Увеличиваем размер кэша
        c.execute(f"PRAGMA cache_size=-{Config.DB_CACHE_SIZE}")
        
        # Создаем таблицу для известных кошельков
        c.execute('''CREATE TABLE IF NOT EXISTS wallets
                     (address TEXT PRIMARY KEY, 
                      balance_usd REAL,
                      tx_count INTEGER,
                      last_active INTEGER,
                      created_at INTEGER)''')
        
        # Создаем индексы для ускорения поиска
        c.execute('''CREATE INDEX IF NOT EXISTS idx_balance_usd ON wallets(balance_usd)''')
        c.execute('''CREATE INDEX IF NOT EXISTS idx_tx_count ON wallets(tx_count)''')
        c.execute('''CREATE INDEX IF NOT EXISTS idx_last_active ON wallets(last_active)''')
        
        conn.commit()
        conn.close()
    
    def add_wallet(self, address, balance_usd=0, tx_count=0, last_active=0):
        """Добавление кошелька в базу данных"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("INSERT OR REPLACE INTO wallets VALUES (?, ?, ?, ?, ?)",
                  (address, balance_usd, tx_count, last_active, int(time.time())))
        
        conn.commit()
        conn.close()
    
    def add_wallets_batch(self, wallets):
        """Пакетное добавление кошельков"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        current_time = int(time.time())
        data = [(address, balance_usd, tx_count, last_active, current_time) 
                for address, balance_usd, tx_count, last_active in wallets]
        
        c.executemany("INSERT OR REPLACE INTO wallets VALUES (?, ?, ?, ?, ?)", data)
        
        conn.commit()
        conn.close()
    
    def is_known(self, address):
        """Проверка, известен ли кошелек"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("SELECT * FROM wallets WHERE address=?", (address,))
        result = c.fetchone()
        
        conn.close()
        return result is not None
    
    def are_known_batch(self, addresses):
        """Пакетная проверка, известны ли кошельки"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        placeholders = ','.join(['?' for _ in addresses])
        query = f"SELECT address FROM wallets WHERE address IN ({placeholders})"
        
        c.execute(query, addresses)
        known_addresses = {row[0] for row in c.fetchall()}
        
        conn.close()
        return {addr: addr in known_addresses for addr in addresses}
    
    def get_active_wallets(self, min_balance_usd=0, min_tx=1, max_inactive_days=365):
        """Получение активных кошельков"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        max_inactive_seconds = max_inactive_days * 24 * 60 * 60
        current_time = int(time.time())
        
        c.execute("SELECT * FROM wallets WHERE balance_usd>=? AND tx_count>=? AND last_active>=?", 
                  (min_balance_usd, min_tx, current_time - max_inactive_seconds))
        result = c.fetchall()
        
        conn.close()
        return result
    
    def import_from_file(self, file_path, wallet_type="eth"):
        """Импорт кошельков из файла"""
        imported = 0
        try:
            with open(file_path, 'r') as f:
                wallets = []
                for line in f:
                    address = line.strip()
                    if address:
                        wallets.append((address, 0, 0, 0))
                        imported += 1
                        # Пакетно добавляем каждые 1000 кошельков
                        if len(wallets) >= 1000:
                            self.add_wallets_batch(wallets)
                            wallets = []
                
                # Добавляем оставшиеся кошельки
                if wallets:
                    self.add_wallets_batch(wallets)
            
            return imported
        except Exception as e:
            print(f"Ошибка импорта из файла {file_path}: {e}")
            return imported

# Глобальный экземпляр базы данных
known_wallets_db = KnownWalletsDB()

"""
Модуль для логирования действий программы.
"""
import logging
from logging.handlers import RotatingFileHandler

class LessVerboseFilter(logging.Filter):
    def filter(self, record):
        # Фильтруем повторяющиеся сообщения о загрузке паттернов
        if "Загружено" in record.getMessage() and "паттернов из" in record.getMessage():
            return False
        return True

class GUIHandler(logging.Handler):
    """Обработчик для вывода логов в GUI"""
    def __init__(self, gui_callback=None):
        super().__init__()
        self.gui_callback = gui_callback
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S'))
    
    def set_gui_callback(self, callback):
        """Установка callback-функции для обновления GUI"""
        self.gui_callback = callback
    
    def emit(self, record):
        try:
            msg = self.format(record)
            if self.gui_callback:
                self.gui_callback(msg)
        except Exception:
            pass

def setup_logger(gui_callback=None):
    """Настройка системы логирования"""
    # Создаем логгер
    logger = logging.getLogger('WalletScanner')
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    
    # Удаляем все существующие обработчики
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Обработчик для вывода в консоль (всегда включаем)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Обработчик для записи в файл
    if Config.LOG_TO_FILE:
        # Создаем директорию для логов, если ее нет
        os.makedirs(os.path.dirname(Config.LOG_FILE), exist_ok=True)
        
        file_handler = RotatingFileHandler(
            Config.LOG_FILE,
            maxBytes=Config.LOG_MAX_SIZE,
            backupCount=Config.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Обработчик для GUI
    gui_handler = GUIHandler(gui_callback)
    gui_handler.setLevel(logging.INFO)
    logger.addHandler(gui_handler)
    
    # Добавляем фильтр для уменьшения verbosity
    verbose_filter = LessVerboseFilter()
    for handler in logger.handlers:
        handler.addFilter(verbose_filter)
    
    return logger

# Глобальный экземпляр логгера
logger = setup_logger()

"""
Оптимизированный исполнитель с пулом потоков и приоритезацией.
"""
from concurrent.futures import ThreadPoolExecutor

class OptimizedExecutor:
    """Оптимизированный исполнитель с пулом потоков и приоритезацией"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(OptimizedExecutor, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.executor = None
        self.max_workers = 100  # Увеличиваем количество рабочих потоков
        self._initialized = True
    
    def start(self):
        """Запуск исполнителя"""
        if self.executor is None:
            self.executor = ThreadPoolExecutor(
                max_workers=self.max_workers,
                thread_name_prefix="wallet_checker"
            )
    
    def stop(self):
        """Остановка исполнителя"""
        if self.executor:
            self.executor.shutdown(wait=False)
            self.executor = None
    
    def submit(self, fn, *args, **kwargs):
        """Добавление задачи в пул"""
        if self.executor is None:
            self.start()
        return self.executor.submit(fn, *args, **kwargs)
    
    def map(self, fn, iterable, timeout=None, chunksize=1):
        """Параллельное выполнение функции для элементов iterable"""
        if self.executor is None:
            self.start()
        return self.executor.map(fn, iterable, timeout=timeout, chunksize=chunksize)

# Глобальный экземпляр
optimized_executor = OptimizedExecutor()

"""
Основной модуль проверки кошельков с асинхронной оптимизацией.
"""
import concurrent.futures
import requests

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
                    
                    # Исправлено: явное преобразование к int
                    if len(valid_words) >= int(Config.MNEMONIC_LENGTH * 0.8):  # Минимум 80% valid слов
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
                # Используем decimals из конфига вместо жестко заданных значений
                decimals = Config.CRYPTOCURRENCIES[currency]["decimals"]
                
                if currency == "BTC":
                    balance = int(response.text) / (10 ** decimals)
                elif currency == "ETH":
                    data = response.json()
                    balance = data.get('balance', 0) / (10 ** decimals)
                elif currency == "LTC":
                    data = response.json()
                    balance = data.get('balance', 0) / (10 ** decimals)
                else:
                    balance = 0
                    
                logger.debug(f"Баланс {currency}: {balance}")
                return balance
                
            return 0
        except Exception as e:
            logger.error(f"Ошибка при проверке баланса {currency}: {e}")
            return 0
    
    def send_opcua_notification(self, result):
        """Отправка уведомления через OPCUA сервер"""
        if not Config.USE_OPCUA_NOTIFICATIONS:
            return
            
        try:
            from opcua import Client
            from opcua.ua import VariantType
            
            client = Client(Config.OPCUA_SERVER_URL)
            client.connect()
            
            # Получаем узел для записи
            node = client.get_node(Config.OPCUA_NODE_ID)
            
            # Формируем данные для отправки
            notification_data = {
                'mnemonic': result['mnemonic'],
                'total_balance_usd': result['total_balance_usd'],
                'timestamp': result['timestamp']
            }
            
            # Отправляем данные
            node.set_value(json.dumps(notification_data))
            client.disconnect()
            
            logger.info("Уведомление отправлено через OPCUA сервер")
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления через OPCUA: {e}")
    
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
                
                result = {
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
                
                # Отправляем уведомление через OPCUA
                self.send_opcua_notification(result)
                
                return result
            
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
                
                result = {
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
                
                # Отправляем уведомление через OPCUA
                self.send_opcua_notification(result)
                
                return result
            
            return None
        except Exception as e:
            return None
    
    def save_results(self, result):
        """Сохранение результатов в файл"""
        try:
            filename = f"{Config.RESULTS_DIR}/wallet_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Результаты сохранены в файл: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Ошибка сохранения результатов: {e}")
            return None
    
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
            logger.debug("Применяем предварительную фильтрацию")
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
                    try:
                        result = future.result()
                        if result is not None:
                            valid_results.append(result)
                    except Exception as e:
                        logger.error(f"Ошибка при проверке кошелька: {e}")
            
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
                        
                        if self.gui_callback and filename:
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

"""
Модуль установки зависимостей и загрузки ресурсов.
Автоматически настраивает окружение для максимальной производительности.
"""
import subprocess
import importlib

def install_package(package_name, import_name=None):
    """Установка пакета с помощью pip с оптимизацией для скорости"""
    if import_name is None:
        import_name = package_name
    
    print(f"📦 Проверка {package_name}...")
    
    try:
        importlib.import_module(import_name)
        print(f"✅ {package_name} уже установлен")
        return True
    except ImportError:
        print(f"❌ {package_name} отсутствует, устанавливаю...")
        
        try:
            cmd = [sys.executable, "-m", "pip", "install", package_name]
            
            # Для Windows используем precompiled wheels
            if sys.platform == "win32":
                cmd.insert(1, "--prefer-binary")
            
            subprocess.check_call(cmd)
            importlib.import_module(import_name)
            print(f"✅ {package_name} успешно установлен")
            return True
        except Exception as e:
            print(f"❌ Ошибка при установке {package_name}: {e}")
            return False

def download_with_retry(url, path, max_retries=3):
    """Загрузка файла с повторными попытками"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            with open(path, 'wb') as f:
                f.write(response.content)
            return True
        except Exception as e:
            print(f"❌ Попытка {attempt + 1}/{max_retries} не удалась: {e}")
            time.sleep(1)
    return False

def download_bip39_wordlists():
    """Загрузка полных словарей BIP-39"""
    print("🌐 Загрузка словарей BIP-39...")
    
    bip39_files = {
        "english.txt": "https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/english.txt",
        "french.txt": "https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/french.txt",
        "spanish.txt": "https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/spanish.txt",
        "italian.txt": "https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/italian.txt",
        "portuguese.txt": "https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/portuguese.txt",
        "czech.txt": "https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/czech.txt"
    }
    
    success_count = 0
    total_files = len(bip39_files)
    
    for filename, url in bip39_files.items():
        file_path = os.path.join(Config.WORDLISTS_DIR, filename)
        if not os.path.exists(file_path):
            if download_with_retry(url, file_path):
                print(f"✅ Загружен: {filename}")
                success_count += 1
            else:
                print(f"❌ Ошибка загрузки: {filename}")
        else:
            print(f"✅ Уже существует: {filename}")
            success_count += 1
    
    return success_count > 0  # Возвращаем True если хотя бы один словарь загружен

def download_common_patterns():
    """Загрузка распространенных паттернов и паролей"""
    print("🌐 Загрузка распространенных паттернов...")
    
    pattern_files = {
        "common_passwords.txt": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-1000000.txt",
        "keyboard_patterns.txt": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Keyboard-Combinations.txt",
        "crypto_patterns.txt": "https://raw.githubusercontent.com/rareweasel/crypto-wordlists/master/patterns.txt",
    }
    
    success_count = 0
    total_files = len(pattern_files)
    
    for filename, url in pattern_files.items():
        file_path = os.path.join(Config.PATTERNS_DIR, filename)
        if not os.path.exists(file_path):
            try:
                if download_with_retry(url, file_path):
                    print(f"✅ Загружен: {filename}")
                    success_count += 1
                else:
                    print(f"❌ Ошибка загрузки: {filename}")
            except Exception as e:
                print(f"❌ Ошибка загрузки: {filename}: {e}")
        else:
            print(f"✅ Уже существует: {filename}")
            success_count += 1
    
    # Создаем базовые файлы, если не удалось загрузить
    for filename in [Config.COMMON_PATTERNS_FILE, Config.KNOWN_PHRASES_FILE]:
        if not os.path.exists(filename):
            try:
                with open(filename, 'w') as f:
                    if filename == Config.COMMON_PATTERNS_FILE:
                        f.write("one two three four five six seven eight nine ten eleven twelve\n")
                    else:
                        f.write("abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about\n")
                print(f"✅ Создан: {filename}")
                success_count += 1
            except Exception as e:
                print(f"❌ Ошибка создания файла {filename}: {e}")
    
    return success_count >= total_files

def optimize_system_settings():
    """Оптимизация системных настроек для повышения производительности"""
    print("⚙️  Оптимизация системных настроек...")
    
    # Настройка переменных окружения для улучшения производительности
    os.environ['PYTHONUNBUFFERED'] = '1'
    os.environ['PYTHONIOENCODING'] = 'UTF-8'
    
    print("✅ Системные настройки оптимизированы")

def check_environment():
    """Полная проверка и подготовка окружения"""
    print("🔍 Проверка окружения...")
    
    # Проверяем и устанавливаем зависимости
    packages = [
        ("requests", None),
        ("ecdsa", None),
        ("base58", None),
        ("pycryptodome", "Crypto"),
        ("Pillow", "PIL"),
        ("aiohttp", None),
    ]
    
    success = True
    for package_name, import_name in packages:
        if not install_package(package_name, import_name):
            success = False
    
    if not success:
        print("\n❌ Не удалось установить некоторые зависимости.")
        print("Попробуйте установить их вручную:")
        print("pip install requests ecdsa base58 pycryptodome Pillow aiohttp")
        return False
    
    # Загружаем словари
    if not download_bip39_wordlists():
        print("\n⚠️  Не удалось загрузить все словари BIP-39.")
        print("Попробуйте запустить скрипт еще раз")
    
    # Загружаем распространенные паттерны
    if not download_common_patterns():
        print("\n⚠️  Не удалось загрузить все файлы с паттернами.")
        print("Будут использоваться базовые паттерны")
    
    # Оптимизируем настройки системы
    optimize_system_settings()
    
    return True

"""
Параллельная система проверки с разделением генерации и проверки
и интеллектуальным планированием запросов.
"""
import queue
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Tuple

@dataclass
class WalletTask:
    mnemonic: str
    language: str
    seed: bytes = None
    addresses: Dict[str, str] = None
    priority: float = 1.0
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.seed is None and self.mnemonic:
            self.seed = mnemonic_to_seed(self.mnemonic, "")
        if self.addresses is None and self.seed is not None:
            self.addresses = {
                'eth': derive_eth_address(self.seed),
                'btc': derive_btc_address(self.seed),
                'ltc': derive_ltc_address(self.seed),
                'xrp': derive_xrp_address(self.seed),
                'bch': derive_bch_address(self.seed),
                'doge': derive_doge_address(self.seed)
            }

class APIPerformanceTracker:
    """Трекер производительности API для интеллектуального планирования"""
    
    def __init__(self):
        self.api_stats = defaultdict(lambda: {
            'success_count': 0,
            'error_count': 0,
            'total_time': 0,
            'last_used': 0,
            'avg_response_time': 0,
            'success_rate': 1.0
        })
        self.api_cooldowns = {}
        
    def update_stats(self, api_url: str, success: bool, response_time: float):
        """Обновление статистики API"""
        stats = self.api_stats[api_url]
        
        if success:
            stats['success_count'] += 1
            stats['total_time'] += response_time
            stats['avg_response_time'] = stats['total_time'] / stats['success_count']
        else:
            stats['error_count'] += 1
        
        total_requests = stats['success_count'] + stats['error_count']
        stats['success_rate'] = stats['success_count'] / total_requests if total_requests > 0 else 1.0
        stats['last_used'] = time.time()
    
    def get_best_api(self, currency: str) -> str:
        """Выбор лучшего API для заданной валюты"""
        apis = Config.CRYPTOCURRENCIES[currency]["api_urls"]
        
        # Фильтруем API на cooldown
        available_apis = []
        for api in apis:
            if api not in self.api_cooldowns or time.time() > self.api_cooldowns[api]:
                available_apis.append(api)
        
        if not available_apis:
            # Если все API на cooldown, используем тот у которого cooldown скоро закончится
            soonest = min(self.api_cooldowns.items(), key=lambda x: x[1])
            return soonest[0]
        
        # Выбираем API с лучшими показателями
        best_api = max(available_apis, key=lambda api: (
            self.api_stats[api]['success_rate'] * 0.7 +
            (1 / (self.api_stats[api]['avg_response_time'] + 0.1)) * 0.3
        ))
        
        return best_api

class ParallelWalletChecker:
    """Параллельная система проверки кошельков"""
    
    def __init__(self, wordlists, result_callback=None):
        self.wordlists = wordlists
        self.result_callback = result_callback
        self.is_running = False
        
        # Очереди для задач
        self.generation_queue = queue.Queue(maxsize=50000)
        self.validation_queue = queue.Queue(maxsize=50000)
        self.checking_queues = {
            currency: queue.Queue(maxsize=5000) for currency in Config.TARGET_CURRENCIES
        }
        self.results_queue = queue.Queue()
        
        # Трекер производительности API
        self.api_tracker = APIPerformanceTracker()
        
        # Статистика
        self.stats = {
            'generated': 0,
            'validated': 0,
            'checked': defaultdict(int),
            'found': 0,
            'errors': 0
        }
        
        # Пул потоков
        self.threads = []
        
    def start(self):
        """Запуск системы"""
        self.is_running = True
        
        # Запускаем генератор
        self.threads.append(threading.Thread(target=self._generator_worker, daemon=True))
        
        # Запускаем валидатор
        self.threads.append(threading.Thread(target=self._validation_worker, daemon=True))
        
        # Запускаем воркеры для каждой валюты
        for currency in Config.TARGET_CURRENCIES:
            for i in range(Config.MAX_WORKERS // len(Config.TARGET_CURRENCIES)):
                self.threads.append(threading.Thread(
                    target=self._checking_worker, 
                    args=(currency,),
                    daemon=True
                ))
        
        # Запускаем обработчик результатов
        self.threads.append(threading.Thread(target=self._results_worker, daemon=True))
        
        # Запускаем все потоки
        for thread in self.threads:
            thread.start()
        
        logger.info("Параллельная система проверки запущена")
    
    def stop(self):
        """Остановка системы"""
        self.is_running = False
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=5.0)
        logger.info("Параллельная система проверки остановлена")
    
    def _generator_worker(self):
        """Воркер для генерации мнемонических фраз"""
        from crypto_utils import generate_human_mnemonic
        
        batch_size = 100
        while self.is_running:
            try:
                # Генерируем пакет мнемонических фраз
                batch = []
                for _ in range(batch_size):
                    lang = random.choice(Config.ENABLED_LANGUAGES)
                    mnemonic = generate_human_mnemonic(self.wordlists[lang], Config.MNEMONIC_LENGTH)
                    
                    # Пропускаем уже проверенные мнемоники
                    if is_mnemonic_checked(mnemonic):
                        continue
                    
                    batch.append(WalletTask(mnemonic, lang))
                
                # Добавляем в очередь генерации
                for task in batch:
                    self.generation_queue.put(task)
                    self.stats['generated'] += 1
                
                # Небольшая пауза чтобы не перегружать систему
                time.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Ошибка в генераторе: {e}")
                time.sleep(1)
    
    def _validation_worker(self):
        """Воркер для валидации и приоритизации задач"""
        from known_wallets import known_wallets_db
        from crypto_utils import enhanced_heuristic_score, assess_mnemonic_quality
        
        while self.is_running:
            try:
                # Берем задачу из очереди генерации
                task = self.generation_queue.get(timeout=1)
                
                # Проверяем валидность мнемонической фразы
                words = task.mnemonic.split()
                if len(words) != len(set(words)) or len(words) != Config.MNEMONIC_LENGTH:
                    continue
                
                # Проверяем что все слова из правильного словаря
                invalid_words = [word for word in words if word not in self.wordlists[task.language]]
                if invalid_words:
                    continue
                
                # Проверяем известные кошельки
                if any(known_wallets_db.is_known(addr) for addr in task.addresses.values()):
                    continue
                
                # Рассчитываем приоритет на основе эвристик
                eth_address = task.addresses['eth']
                address_score = enhanced_heuristic_score(eth_address, task.mnemonic)
                mnemonic_score = assess_mnemonic_quality(task.mnemonic)
                task.priority = address_score + mnemonic_score
                
                # Добавляем в очередь проверки для каждой валюты
                for currency in Config.TARGET_CURRENCIES:
                    self.checking_queues[currency].put(task)
                
                self.stats['validated'] += 1
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Ошибка в валидаторе: {e}")
                self.stats['errors'] += 1
    
    def _checking_worker(self, currency: str):
        """Воркер для проверки конкретной валюты"""
        while self.is_running:
            try:
                # Берем задачу из очереди для этой валюты
                task = self.checking_queues[currency].get(timeout=1)
                
                # Получаем адрес для этой валюты
                if currency in ["ETH", "USDT_ETH"]:
                    address = task.addresses["eth"]
                else:
                    address = task.addresses["btc"]
                
                # Выбираем лучший API для проверки
                api_url = self.api_tracker.get_best_api(currency)
                full_url = api_url.format(address)
                
                # Выполняем запрос
                start_time = time.time()
                success, balance = self._check_balance(currency, full_url)
                response_time = time.time() - start_time
                
                # Обновляем статистику API
                self.api_tracker.update_stats(api_url, success, response_time)
                
                if success and balance > 0:
                    # Если нашли баланс, добавляем в очередь результатов
                    self.results_queue.put({
                        'currency': currency,
                        'task': task,
                        'balance': balance,
                        'address': address
                    })
                
                # Помечаем мнемоническую фразу как проверенную
                add_checked_mnemonic(task.mnemonic)
                
                self.stats['checked'][currency] += 1
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Ошибка в проверяющем воркере ({currency}): {e}")
                self.stats['errors'] += 1
    
    def _check_balance(self, currency: str, url: str) -> Tuple[bool, float]:
        """Проверка баланса для конкретной валюты"""
        try:
            import requests
            response = requests.get(url, timeout=Config.REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                decimals = Config.CRYPTOCURRENCIES[currency]["decimals"]
                
                if currency == "BTC":
                    balance = int(response.text) / (10 ** decimals)
                elif currency == "ETH":
                    data = response.json()
                    balance = data.get('balance', 0) / (10 ** decimals)
                elif currency == "USDT_ETH":
                    data = response.json()
                    result = data.get('result', '0')
                    balance = int(result) / (10 ** decimals) if data.get('status') == '1' else 0
                elif currency == "LTC":
                    data = response.json()
                    balance = data.get('balance', 0) / (10 ** decimals)
                elif currency == "XRP":
                    data = response.json()
                    balance = float(data.get('xrp_balance', 0))
                elif currency == "BCH":
                    data = response.json()
                    balance = float(data.get('balance', 0)) / (10 ** decimals)
                elif currency == "DOGE":
                    data = response.json()
                    balance = data.get('balance', 0) / (10 ** decimals)
                else:
                    balance = 0
                
                return True, balance
            else:
                return False, 0
                
        except Exception as e:
            logger.debug(f"Ошибка проверки баланса {currency}: {e}")
            return False, 0
    
    def _results_worker(self):
        """Обработчик результатов"""
        from known_wallets import known_wallets_db
        
        accumulated_results = defaultdict(lambda: defaultdict(float))
        
        while self.is_running:
            try:
                # Берем результат из очереди
                result = self.results_queue.get(timeout=1)
                
                currency = result['currency']
                task = result['task']
                balance = result['balance']
                address = result['address']
                
                # Накопляем результаты для каждого кошелька
                wallet_key = task.mnemonic
                accumulated_results[wallet_key][currency] = balance
                accumulated_results[wallet_key]['task'] = task
                accumulated_results[wallet_key]['addresses'] = task.addresses
                
                # Проверяем если у нас есть результаты для всех валют
                if len(accumulated_results[wallet_key]) == len(Config.TARGET_CURRENCIES) + 2:  # +2 для task и addresses
                    # Рассчитываем общий баланс
                    total_balance = 0
                    for curr, bal in accumulated_results[wallet_key].items():
                        if curr not in ['task', 'addresses']:
                            rate = Config.exchange_rates.get(curr, 0)
                            total_balance += bal * rate
                    
                    if total_balance >= Config.MIN_TOTAL_BALANCE_USD:
                        # Сохраняем результат
                        task = accumulated_results[wallet_key]['task']
                        addresses = accumulated_results[wallet_key]['addresses']
                        
                        result_data = {
                            'mnemonic': task.mnemonic,
                            'language': task.language,
                            'addresses': addresses,
                            'balances': {k: v for k, v in accumulated_results[wallet_key].items() 
                                        if k not in ['task', 'addresses']},
                            'total_balance_usd': total_balance,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        # Сохраняем в известные кошельки
                        for addr in addresses.values():
                            known_wallets_db.add_wallet(addr, total_balance)
                        
                        # Вызываем callback если есть
                        if self.result_callback:
                            self.result_callback(result_data)
                        
                        self.stats['found'] += 1
                        logger.info(f"Найден кошелек с балансом ${total_balance:.2f}")
                    
                    # Удаляем обработанный результат
                    del accumulated_results[wallet_key]
                
            except queue.Empty:
                # Проверяем старые результаты (на случай если какие-то валюты не ответили)
                current_time = time.time()
                keys_to_remove = []
                
                for key, data in accumulated_results.items():
                    task = data.get('task')
                    if task and current_time - task.created_at > Config.REQUEST_TIMEOUT * 3:
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    del accumulated_results[key]
                
                continue
            except Exception as e:
                logger.error(f"Ошибка в обработчике результатов: {e}")
                self.stats['errors'] += 1

    def get_stats(self) -> Dict:
        """Получение текущей статистики"""
        return self.stats.copy()

"""
Инструменты для ручной проверки мнемонических фраз.
"""
def check_single_mnemonic(mnemonic, lang="english"):
    """Проверка одной мнемонической фразы"""
    print(f"Проверка мнемонической фразы: {mnemonic}")
    print(f"Язык: {lang}")
    logger.info(f"Ручная проверка мнемонической фразы: {mnemonic}")
    
    try:
        # Преобразуем мнемоническую фразу в seed
        seed = mnemonic_to_seed(mnemonic, "")
        print(f"Seed: {seed.hex()}")
        logger.debug(f"Seed: {seed.hex()}")
        
        # Генерируем адреса
        eth_address = derive_eth_address(seed)
        btc_address = derive_btc_address(seed)
        print(f"ETH адрес: {eth_address}")
        print(f"BTC адрес: {btc_address}")
        logger.debug(f"ETH адрес: {eth_address}")
        logger.debug(f"BTC адрес: {btc_address}")
        
        # Проверяем балансы
        addresses = {"eth": eth_address, "btc": btc_address}
        balance_data = check_balances_batch_async(addresses).result()
        
        print("\nРезультаты проверки:")
        print(f"Общий баланс: ${balance_data['total_usd']:.2f} USD")
        logger.info(f"Общий баланс: ${balance_data['total_usd']:.2f} USD")
        
        for currency, balance in balance_data['crypto_balances'].items():
            if balance > 0:
                usd_balance = balance_data['usd_balances'][currency]
                print(f"{currency}: {balance} (${usd_balance:.2f})")
                logger.info(f"{currency}: {balance} (${usd_balance:.2f})")
        
        return balance_data
        
    except Exception as e:
        print(f"Ошибка при проверке мнемонической фразы: {e}")
        logger.error(f"Ошибка при проверке мнемонической фразы: {e}")
        return None

def check_multiple_mnemonics(mnemonics, lang="english"):
    """Проверка нескольких мнемонических фраз"""
    results = []
    
    for i, mnemonic in enumerate(mnemonics):
        print(f"\n--- Проверка фразы {i+1}/{len(mnemonics)} ---")
        logger.info(f"Ручная проверка мнемонической фразы {i+1}/{len(mnemonics)}")
        result = check_single_mnemonic(mnemonic, lang)
        results.append(result)
    
    return results

if __name__ == "__main__":
    # Пример использования
    test_mnemonics = [
        "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about",
        "legal winner thank year wave sausage worth useful legal winner thank yellow"
    ]
    
    check_multiple_mnemonics(test_mnemonics)

"""
Главный модуль приложения.
Точка входа с оптимизацией запуска и обработки ошибок.
"""
import traceback

def main():
    """Основная функция с обработкой ошибков и оптимизацией"""
    try:
        # Перенастраиваем логгер для GUI перед инициализацией
        Config.LOG_TO_CONSOLE = True  # Убедимся, что вывод в консоль включен
        
        logger.info("Запуск приложения Wallet Scanner")
        
        # Загрузка настроек
        Config.load_settings()
        logger.info("Настройки загружены")
        
        # Проверка и подготовка окружения
        from installer import check_environment
        if not check_environment():
            logger.error("Ошибка подготовки окружения!")
            print("Ошибка подготовки окружения!")
            print("Пожалуйста, установите необходимые зависимости:")
            print("pip install requests ecdsa base58 pycryptodome Pillow aiohttp")
            input("Нажмите Enter для выхода...")
            sys.exit(1)
        
        # Проверка словарей BIP-39
        if not os.path.exists(Config.WORDLISTS_DIR) or not os.listdir(Config.WORDLISTS_DIR):
            logger.error("Словари BIP-39 не найдены!")
            print("Словари BIP-39 не найдены!")
            response = input("Загрузить словари? (y/n): ")
            if response.lower() == 'y':
                from installer import download_bip39_wordlists
                if not download_bip39_wordlists():
                    logger.error("Не удалось загрузить словари!")
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
                logger.info(f"Загружен словарь {lang}: {len(wordlists[lang])} слов")
            else:
                logger.error(f"Словарь {lang} не найден!")
                print(f"Словарь {lang} не найден!")

        # Если нет ни одного словаря, выходим
        if not wordlists:
            logger.error("Не загружено ни одного словаря BIP-39!")
            print("Не загружено ни одного словаря BIP-39!")
            sys.exit(1)

        # Проверяем, что словари содержат достаточно слов
        for lang, words in wordlists.items():
            if len(words) < 2048:
                logger.error(f"Словарь {lang} содержит недостаточно слов: {len(words)} вместо 2048")
                print(f"Словарь {lang} содержит недостаточно слов: {len(words)} вместо 2048")

        # Обновляем список доступных языков
        Config.ENABLED_LANGUAGES = list(wordlists.keys())
        
        # Импорты после проверки окружения
        from quantum_gui import QuantumWalletGUI
        from async_manager import async_manager
        
        # Запуск GUI
        root = tk.Tk()
        app = QuantumWalletGUI(root)
        logger.info("GUI инициализирован")
        
        # Обработка закрытия окна
        def on_closing():
            if hasattr(app, 'is_running') and app.is_running:
                import tkinter.messagebox as messagebox
                if messagebox.askokcancel("Выход", "Проверка активна. Вы уверены, что хотите выйти?"):
                    logger.info("Остановка проверки и выход из приложения")
                    app.stop_checking()
                    # Останавливаем менеджер асинхронных операций
                    async_manager.stop()
                    root.destroy()
            else:
                # Останавливаем менеджер асинхронных операций
                async_manager.stop()
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        logger.info("Запуск основного цикла приложения")
        root.mainloop()
        
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")
        logger.critical(traceback.format_exc())
        print(f"Критическая ошибка: {e}")
        traceback.print_exc()
        input("Нажмите Enter для выхода...")
        sys.exit(1)

if __name__ == "__main__":
    main()
