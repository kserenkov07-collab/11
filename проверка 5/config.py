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
                "https://mempool.space/api/address/{}"
            ],
            "api_keys": [],
            "decimals": 8
        },
        "ETH": {
            "name": "Ethereum", 
            "api_urls": [
                "https://api.blockcypher.com/v1/eth/main/addrs/{}/balance",
                "https://api.etherscan.io/api?module=account&action=balance&address={}&tag=latest",
                "https://blockscout.com/eth/mainnet/api?module=account&action=balance&address={}"
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
    MAX_WORKERS = min(multiprocessing.cpu_count() * 3, 300)
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
    KNOWN_PHRASES_FILE = os.path.join(PATTERNS_DIR, "known_phrases.txt")
    COMMON_PASSWORDS_FILE = os.path.join(PATTERNS_DIR, "common_passwords.txt")
    KEYBOARD_PATTERNS_FILE = os.path.join(PATTERNS_DIR, "keyboard_patterns.txt")
    CRYPTO_PATTERNS_FILE = os.path.join(PATTERNS_DIR, "crypto_patterns.txt")
    KNOWN_MNEMONICS_FILE = os.path.join(PATTERNS_DIR, "known_mnemonics.txt")

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
    LOG_LEVEL = 'DEBUG'
    LOG_TO_FILE = True
    LOG_TO_CONSOLE = False  # Отключаем вывод в консоль по умолчанию
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

    @classmethod
    def init_directories(cls):
        """Создание необходимых директорий"""
        for directory in [cls.RESULTS_DIR, cls.CACHE_DIR, cls.LOG_DIR, cls.WORDLISTS_DIR, cls.PATTERNS_DIR]:
            os.makedirs(directory, exist_ok=True)

        # Создаем файлы с общими паттернами, если их нет
        for file_path in [cls.COMMON_PATTERNS_FILE, cls.KNOWN_PHRASES_FILE, cls.COMMON_PASSWORDS_FILE, 
                         cls.KEYBOARD_PATTERNS_FILE, cls.CRYPTO_PATTERNS_FILE, cls.KNOWN_MNEMONICS_FILE]:
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    if file_path == cls.COMMON_PASSWORDS_FILE:
                        f.write("password\n123456\nqwerty\nadmin\nletmein\nwelcome\nmonkey\n")
                    elif file_path == cls.KEYBOARD_PATTERNS_FILE:
                        f.write("qwerty\nasdfgh\nzxcvbn\n123456\n!@#$%^\n")
                    elif file_path == cls.COMMON_PATTERNS_FILE:
                        f.write("one two three four five six seven eight nine ten eleven twelve\n")
                        f.write("alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu\n")
                    elif file_path == cls.KNOWN_PHRASES_FILE:
                        f.write("abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about\n")
                    elif file_path == cls.CRYPTO_PATTERNS_FILE:
                        f.write("bitcoin ethereum wallet private key seed phrase\n")
                        f.write("crypto blockchain address transaction\n")
                    elif file_path == cls.KNOWN_MNEMONICS_FILE:
                        f.write("# Добавьте известные мнемонические фразы здесь, каждую на новой строке\n")

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
                'LOG_TO_CONSOLE': cls.LOG_TO_CONSOLE
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
