"""
Конфигурационный модуль с настройками приложения.
Включает параметры API, лимиты проверки и пути к ресурсам.
Оптимизирован для максимальной производительности.
"""
import os
import json
import multiprocessing

class Config:
    """Класс для управления настройками приложения"""
    
    # Настройки криптовалют и API
    CRYPTOCURRENCIES = {
        "BTC": {
            "name": "Bitcoin", 
            "api_url": "https://blockchain.info/q/addressbalance/{}",
            "api_url_backup": "https://api.blockcypher.com/v1/btc/main/addrs/{}/balance",
            "api_keys": []
        },
        "ETH": {
            "name": "Ethereum", 
            "api_url": "https://api.blockcypher.com/v1/eth/main/addrs/{}/balance",
            "api_url_backup": "https://api.etherscan.io/api?module=account&action=balance&address={}&tag=latest",
            "api_keys": []
        },
        "USDT_ETH": {
            "name": "Tether (Ethereum)", 
            "api_url": "https://api.etherscan.io/api?module=account&action=tokenbalance&contractaddress=0xdac17f958d2ee523a2206206994597c13d831ec7&address={}",
            "api_keys": []
        },
        "USDT_TRON": {
            "name": "Tether (TRON)", 
            "api_url": "https://api.trongrid.io/v1/accounts/{}",
            "api_keys": []
        },
        "BNB": {
            "name": "Binance Coin", 
            "api_url": "https://api.bscscan.com/api?module=account&action=balance&address={}",
            "api_keys": []
        },
        "USDT_BSC": {
            "name": "Tether (BSC)", 
            "api_url": "https://api.bscscan.com/api?module=account&action=tokenbalance&contractaddress=0x55d398326f99059ff775485246999027b3197955&address={}",
            "api_keys": []
        },
        "ADA": {
            "name": "Cardano", 
            "api_url": "https://cardano-mainnet.blockfrost.io/api/v0/addresses/{}",
            "api_keys": []
        },
        "SOL": {
            "name": "Solana", 
            "api_url": "https://public-api.solscan.io/account/{}",
            "api_keys": []
        },
        "LTC": {
            "name": "Litecoin", 
            "api_url": "https://api.blockchair.com/litecoin/dashboards/address/{}",
            "api_keys": []
        },
        "XRP": {
            "name": "Ripple", 
            "api_url": "https://api.xrpscan.com/api/v1/account/{}",
            "api_keys": []
        },
        "DOGE": {
            "name": "Dogecoin", 
            "api_url": "https://api.blockcypher.com/v1/doge/main/addrs/{}/balance",
            "api_keys": []
        }
    }

    # Параметры проверки (оптимизированы для скорости)
    MIN_BALANCE = 0.0001
    MIN_TOTAL_BALANCE_USD = 1.0  # Уменьшено для тестирования
    MIN_TX_COUNT = 1  # Минимальное количество транзакций для активного кошелька
    MIN_INACTIVE_DAYS = 90  # Минимальное количество дней бездействия
    MAX_WORKERS = min(multiprocessing.cpu_count() * 3, 300)  # Умное определение
    BATCH_SIZE = 1000  # Увеличено для производительности
    REQUEST_TIMEOUT = 15  # Увеличено для стабильности
    CACHE_EXPIRY = 3600  # Увеличено до 1 часа
    ZERO_BALANCE_CACHE_EXPIRY = 86400  # 24 часа для нулевых балансов

    # Параметры двухэтапной проверки
    PRIMARY_CURRENCIES = ["BTC", "ETH"]  # Валюты для первоначальной проверки
    MIN_PRIMARY_BALANCE_USD = 0.1  # Минимальный баланс в основных валютах для продолжения проверки
    PRIMARY_CHECK_TIMEOUT = 5  # Таймаут для проверки основных валют

    # Настройки путей
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    WORDLISTS_DIR = os.path.join(BASE_DIR, "bip39-wordlists")
    RESULTS_DIR = os.path.join(BASE_DIR, "found_wallets")
    CACHE_DIR = os.path.join(BASE_DIR, "cache")
    LOG_DIR = os.path.join(BASE_DIR, "logs")
    PATTERNS_DIR = os.path.join(BASE_DIR, "patterns")

    # Новые настройки для улучшенной генерации
    USE_HUMAN_PATTERNS = True  # Включено для увеличения шанса находки
    USE_TX_ACTIVITY_CHECK = True  # Проверка активности кошелька
    USE_MULTIPLE_API_SOURCES = True  # Использование нескольких API источников
    USE_BATCH_API = True  # Использовать пакетные API запросы
    USE_PREFILTERING = True  # Использовать предварительную фильтрацию
    USE_PRIORITIZATION = True  # Использовать приоритизацию
    PREFILTER_THRESHOLD = 10  # Увеличено для более строгой фильтрации
    COMMON_PATTERNS_FILE = os.path.join(PATTERNS_DIR, "common_patterns.txt")
    KNOWN_PHRASES_FILE = os.path.join(PATTERNS_DIR, "known_phrases.txt")
    COMMON_PASSWORDS_FILE = os.path.join(PATTERNS_DIR, "common_passwords.txt")
    KEYBOARD_PATTERNS_FILE = os.path.join(PATTERNS_DIR, "keyboard_patterns.txt")
    KNOWN_MNEMONICS_FILE = os.path.join(PATTERNS_DIR, "known_mnemonics.txt")  # Новый файл

    # Настройки базы данных известных кошельков
    KNOWN_WALLETS_DB = os.path.join(BASE_DIR, "known_wallets.db")
    DB_CACHE_SIZE = 20000  # Увеличено до 20MB
    DB_JOURNAL_MODE = "WAL"  # Режим журналирования

    # Целевые криптовалюты для проверки
    TARGET_CURRENCIES = ["BTC", "ETH", "USDT_ETH", "BNB"]

    # Настройки производительности
    USE_PERSISTENT_CACHE = True
    MAX_RETRIES = 5  # Увеличено для надежности
    RETRY_DELAY = 0.5
    RETRY_BACKOFF = 2.0  # Экспоненциальная задержка

    # Коэффициенты для эвристической оценки
    HEURISTIC_WEIGHTS = {
        'pattern_score': 0.5,
        'tx_activity': 0.2,
        'balance_score': 0.3,
        'mnemonic_quality': 0.4  # Новый параметр
    }

    # Новые настройки для длины мнемонической фразы и языков
    MNEMONIC_LENGTH = 12  # 12, 15, 18, 21, 24
    ENABLED_LANGUAGES = ['english']  # Список включенных языков

    # Файл для сохранения настроек
    SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

    # Настройки API ключей
    API_KEYS_FILE = os.path.join(BASE_DIR, "api_keys.json")

    # Настройки логирования
    LOG_LEVEL = 'DEBUG'  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_TO_FILE = True
    LOG_FILE = os.path.join(LOG_DIR, "wallet_scanner.log")
    LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5

    # Курсы валют по умолчанию (будут обновляться автоматически)
    exchange_rates = {
        'BTC': 50000,
        'ETH': 3000,
        'USDT': 1,
        'BNB': 400
    }

    @classmethod
    def init_directories(cls):
        """Создание необходимых директорий"""
        for directory in [cls.RESULTS_DIR, cls.CACHE_DIR, cls.LOG_DIR, cls.WORDLISTS_DIR, cls.PATTERNS_DIR]:
            os.makedirs(directory, exist_ok=True)

        # Создаем файлы с общими паттернами, если их нет
        for file_path in [cls.COMMON_PATTERNS_FILE, cls.KNOWN_PHRASES_FILE, cls.COMMON_PASSWORDS_FILE, 
                         cls.KEYBOARD_PATTERNS_FILE, cls.KNOWN_MNEMONICS_FILE]:
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
                'PREFILTER_THRESHOLD': cls.PREFILTER_THRESHOLD,
                'TARGET_CURRENCIES': cls.TARGET_CURRENCIES,
                'PRIMARY_CURRENCIES': cls.PRIMARY_CURRENCIES,
                'MIN_PRIMARY_BALANCE_USD': cls.MIN_PRIMARY_BALANCE_USD,
                'PRIMARY_CHECK_TIMEOUT': cls.PRIMARY_CHECK_TIMEOUT,
                'LOG_LEVEL': cls.LOG_LEVEL,
                'LOG_TO_FILE': cls.LOG_TO_FILE
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
