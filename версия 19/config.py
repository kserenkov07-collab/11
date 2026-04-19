"""
Конфигурационный модуль приложения.
"""
import json
import os
import multiprocessing
import threading
from typing import Dict, List, Any
from dataclasses import dataclass, asdict, field
import orjson

@dataclass
class AppConfig:
    # Основные настройки
    PRIMARY_WORKERS: int = 10
    CHILD_WORKERS: int = 90
    PROCESS_POOL_WORKERS: int = field(default_factory=lambda: max(2, multiprocessing.cpu_count() // 2))
    MNEMONIC_LENGTH: int = 12
    MIN_TOTAL_BALANCE_USD: float = 0.01
    
    # Настройки производительности
    REQUEST_TIMEOUT: int = 8
    MAX_RETRIES: int = 2
    RETRY_DELAY: float = 0.2
    BATCH_SIZE: int = 100
    QUEUE_SIZE: int = 50000
    MAX_CONCURRENT_REQUESTS: int = 200
    CACHE_SIZE: int = 500000
    CACHE_EXPIRY: int = 3600
    
    # Директории
    BASE_DIR: str = field(default_factory=lambda: os.path.dirname(os.path.abspath(__file__)))
    WORDLISTS_DIR: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.abspath(__file__)), "wordlists"))
    RESULTS_DIR: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"))
    LOGS_DIR: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs"))
    CACHE_DIR: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache"))
    
    # Файлы
    CONFIG_FILE: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json"))
    CHECKED_MNEMONICS_FILE: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.abspath(__file__)), "checked_mnemonics.msgpack"))
    
    # Настройки по умолчанию
    ENABLED_LANGUAGES: List[str] = field(default_factory=lambda: ["english", "french", "spanish", "italian", "portuguese"])
    TARGET_CURRENCIES: List[str] = field(default_factory=lambda: ["BTC", "ETH", "BSC", "LTC", "XRP", "BCH", "DOGE"])
    API_PROVIDERS: Dict[str, List[str]] = field(default_factory=lambda: {
        "BTC": [
            "https://blockchain.info/q/addressbalance/{address}",
            "https://api.blockcypher.com/v1/btc/main/addrs/{address}/balance",
        ],
        "ETH": [
            "https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest",
            "https://api.blockcypher.com/v1/eth/main/addrs/{address}/balance",
        ],
        "BSC": [
            "https://api.bscscan.com/api?module=account&action=balance&address={address}&tag=latest",
        ],
        "LTC": [
            "https://api.blockcypher.com/v1/ltc/main/addrs/{address}/balance",
        ],
        "XRP": [
            "https://data.ripple.com/v2/accounts/{address}/balances",
        ],
        "BCH": [
            "https://blockdozer.com/api/addr/{address}",
        ],
        "DOGE": [
            "https://sochain.com/api/v2/get_address/DOGE/{address}",
        ]
    })
    EXCHANGE_RATES: Dict[str, float] = field(default_factory=lambda: {
        "BTC": 50000, "ETH": 3000, "BSC": 3000, 
        "LTC": 150, "XRP": 0.5, "BCH": 400, "DOGE": 0.1
    })
    
    # Настройки логирования
    LOG_LEVEL: str = "INFO"
    LOG_TO_FILE: bool = True
    LOG_TO_CONSOLE: bool = True
    
    # Дополнительные настройки
    USE_SELENIUM: bool = False  # Использовать Selenium для сложных случаев
    OPCUA_ENDPOINT: str = ""  # Endpoint OPC UA сервера для мониторинга
    MAX_MEMORY_USAGE: int = 0  # Максимальное использование памяти в MB (0 - не ограничивать)

    def __post_init__(self):
        # Создаем необходимые директории
        os.makedirs(self.WORDLISTS_DIR, exist_ok=True)
        os.makedirs(self.RESULTS_DIR, exist_ok=True)
        os.makedirs(self.LOGS_DIR, exist_ok=True)
        os.makedirs(self.CACHE_DIR, exist_ok=True)

class Config:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._config = AppConfig()
                cls._instance.load_settings()
            return cls._instance
    
    def __getattr__(self, name):
        return getattr(self._config, name)
    
    def load_settings(self):
        """Загрузка настроек из файла"""
        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'rb') as f:
                    settings = orjson.loads(f.read())
                
                for key, value in settings.items():
                    if hasattr(self._config, key):
                        setattr(self._config, key, value)
        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")
    
    def save_settings(self):
        """Сохранение настроек в файл"""
        try:
            settings = asdict(self._config)
            with open(self.CONFIG_FILE, 'wb') as f:
                f.write(orjson.dumps(settings, option=orjson.OPT_INDENT_2))
        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")
    
    def update_settings(self, new_settings: Dict[str, Any]):
        """Обновление настроек"""
        for key, value in new_settings.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
        
        self.save_settings()

# Глобальный экземпляр конфигурации
config = Config()