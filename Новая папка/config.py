"""
Конфигурационный модуль с настройками приложения.
Включает параметры API, лимиты проверки и пути к ресурсам.
Оптимизирован для максимальной производительности.
"""
import os
import json

class Config:
    """Класс для управления настройками приложения"""
    
    # Настройки криптовалют и API
    CRYPTOCURRENCIES = {
        "BTC": {
            "name": "Bitcoin", 
            "api_url": "https://blockchain.info/q/addressbalance/{}",
            "api_url_backup": "https://api.blockcypher.com/v1/btc/main/addrs/{}/balance"
        },
        "ETH": {
            "name": "Ethereum", 
            "api_url": "https://api.etherscan.io/api?module=account&action=balance&address={}&tag=latest",
            "api_url_backup": "https://api.blockcypher.com/v1/eth/main/addrs/{}/balance"
        },
        "USDT_ETH": {
            "name": "Tether (Ethereum)", 
            "api_url": "https://api.etherscan.io/api?module=account&action=tokenbalance&contractaddress=0xdac17f958d2ee523a2206206994597c13d831ec7&address={}&tag=latest"
        },
        "USDT_TRON": {
            "name": "Tether (TRON)", 
            "api_url": "https://api.trongrid.io/v1/accounts/{}"
        },
        "BNB": {
            "name": "Binance Coin", 
            "api_url": "https://api.bscscan.com/api?module=account&action=balance&address={}&tag=latest"
        },
        "USDT_BSC": {
            "name": "Tether (BSC)", 
            "api_url": "https://api.bscscan.com/api?module=account&action=tokenbalance&contractaddress=0x55d398326f99059ff775485246999027b3197955&address={}&tag=latest"
        },
        "ADA": {
            "name": "Cardano", 
            "api_url": "https://cardano-mainnet.blockfrost.io/api/v0/addresses/{}"
        },
        "SOL": {
            "name": "Solana", 
            "api_url": "https://public-api.solscan.io/account/{}"
        },
        "LTC": {
            "name": "Litecoin", 
            "api_url": "https://api.blockchair.com/litecoin/dashboards/address/{}"
        },
        "XRP": {
            "name": "Ripple", 
            "api_url": "https://api.xrpscan.com/api/v1/account/{}"
        },
        "DOGE": {
            "name": "Dogecoin", 
            "api_url": "https://api.blockcypher.com/v1/doge/main/addrs/{}/balance"
        }
    }

    # Параметры проверки (оптимизированы для скорости)
    MIN_BALANCE = 0.0001
    MIN_TOTAL_BALANCE_USD = 1.0  # Уменьшено для тестирования
    MIN_TX_COUNT = 1  # Минимальное количество транзакций для активного кошелька
    MIN_INACTIVE_DAYS = 90  # Минимальное количество дней бездействия
    MAX_WORKERS = 200  # Увеличено для максимальной производительности
    BATCH_SIZE = 500  # Увеличенный размер пакета
    REQUEST_TIMEOUT = 10  # Оптимальный таймаут
    CACHE_EXPIRY = 600  # Увеличенное время жизни кэша

    # Настройки путей
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    WORDLISTS_DIR = os.path.join(BASE_DIR, "bip39-wordlists")
    RESULTS_DIR = os.path.join(BASE_DIR, "found_wallets")
    CACHE_DIR = os.path.join(BASE_DIR, "cache")
    LOG_DIR = os.path.join(BASE_DIR, "logs")
    PATTERNS_DIR = os.path.join(BASE_DIR, "patterns")

    # Новые настройки для улучшенной генерации
    USE_HUMAN_PATTERNS = False  # Отключено для чистоты BIP-39
    USE_TX_ACTIVITY_CHECK = True  # Проверка активности кошелька
    USE_MULTIPLE_API_SOURCES = True  # Использование нескольких API источников
    USE_BATCH_API = True  # Использовать пакетные API запросы
    USE_PREFILTERING = True  # Использовать предварительную фильтрацию
    PREFILTER_THRESHOLD = 5  # Порог для предварительной фильтрации
    COMMON_PATTERNS_FILE = os.path.join(PATTERNS_DIR, "common_patterns.txt")
    KNOWN_PHRASES_FILE = os.path.join(PATTERNS_DIR, "known_phrases.txt")
    COMMON_PASSWORDS_FILE = os.path.join(PATTERNS_DIR, "common_passwords.txt")
    KEYBOARD_PATTERNS_FILE = os.path.join(PATTERNS_DIR, "keyboard_patterns.txt")

    # Настройки базы данных известных кошельков
    KNOWN_WALLETS_DB = os.path.join(BASE_DIR, "known_wallets.db")
    DB_CACHE_SIZE = 10000  # Размер кэша БД (10MB)
    DB_JOURNAL_MODE = "WAL"  # Режим журналирования

    # Целевые криптовалюты для проверки (сокращенный список для скорости)
    TARGET_CURRENCIES = ["BTC", "ETH", "USDT_ETH", "BNB"]

    # Настройки производительности
    USE_PERSISTENT_CACHE = True
    MAX_RETRIES = 3  # Уменьшено для скорости
    RETRY_DELAY = 0.5

    # Коэффициенты для эвристической оценки
    HEURISTIC_WEIGHTS = {
        'pattern_score': 0.4,
        'tx_activity': 0.3,
        'balance_score': 0.3
    }

    # Новые настройки для длины мнемонической фразы и языков
    MNEMONIC_LENGTH = 12  # 12, 15, 18, 21, 24
    ENABLED_LANGUAGES = ['english']  # Список включенных языков

    # Файл для сохранения настроек
    SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

    @classmethod
    def init_directories(cls):
        """Создание необходимых директорий"""
        for directory in [cls.RESULTS_DIR, cls.CACHE_DIR, cls.LOG_DIR, cls.WORDLISTS_DIR, cls.PATTERNS_DIR]:
            os.makedirs(directory, exist_ok=True)

        # Создаем файлы с общими паттернами, если их нет
        for file_path in [cls.COMMON_PATTERNS_FILE, cls.KNOWN_PHRASES_FILE, cls.COMMON_PASSWORDS_FILE, cls.KEYBOARD_PATTERNS_FILE]:
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
                'PREFILTER_THRESHOLD': cls.PREFILTER_THRESHOLD,
                'TARGET_CURRENCIES': cls.TARGET_CURRENCIES
            }
            
            with open(cls.SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")

# Инициализация директорий
Config.init_directories()

# Загрузка настроек при импорте модуля
Config.load_settings()

# Создаем экземпляр конфигурации для обратной совместимости
config = Config()
