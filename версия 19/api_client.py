"""
Модуль для работы с API блокчейнов.
"""
import asyncio
import time
import orjson
from typing import Dict, List, Optional
import aiohttp
import async_timeout
from aiohttp import ClientSession, TCPConnector
from config import config
from logger import logger

# Установка uvloop для повышения производительности asyncio
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    logger.warning("uvloop не установлен, используется стандартный asyncio")

class CachedResponse:
    __slots__ = ('data', 'timestamp')
    
    def __init__(self, data, timestamp):
        self.data = data
        self.timestamp = timestamp

class OptimizedAPIClient:
    """Оптимизированный API клиент с кэшированием и балансировкой нагрузки"""
    
    def __init__(self):
        self.session: ClientSession = None
        self.response_cache: Dict[str, CachedResponse] = {}
        self.provider_stats: Dict[str, Dict] = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self.cache_lock = threading.RLock()
    
    async def __aenter__(self):
        # Оптимизированные настройки соединения
        connector = TCPConnector(
            limit=config.MAX_CONCURRENT_REQUESTS,
            limit_per_host=config.MAX_CONCURRENT_REQUESTS // 2,
            ttl_dns_cache=300,
            use_dns_cache=True,
            enable_cleanup_closed=True
        )
        
        self.session = ClientSession(
            connector=connector,
            json_serialize=lambda x: orjson.dumps(x).decode(),
            timeout=aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        
        # Логируем статистику кэша
        total = self.cache_hits + self.cache_misses
        if total > 0:
            hit_ratio = self.cache_hits / total * 100
            logger.info(f"Статистика кэша: {self.cache_hits}/{total} ({hit_ratio:.1f}% hit rate)")
    
    async def check_balances(self, addresses: Dict[str, str]) -> Dict[str, float]:
        """Проверка балансов для всех адресов с использованием кэша"""
        tasks = []
        address_keys = []
        
        for currency, address in addresses.items():
            cache_key = f"{currency}:{address}"
            
            # Проверяем кэш
            with self.cache_lock:
                cached_response = self.response_cache.get(cache_key)
                if cached_response and time.time() - cached_response.timestamp < config.CACHE_EXPIRY:
                    self.cache_hits += 1
                    tasks.append(asyncio.sleep(0))  # Пустая задача для сохранения порядка
                    address_keys.append((currency, address, True))
                    continue
            
            self.cache_misses += 1
            address_keys.append((currency, address, False))
            tasks.append(self._check_balance(currency, address))
        
        # Выполняем все задачи параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обрабатываем результаты
        balances = {}
        result_idx = 0
        
        for currency, address, is_cached in address_keys:
            if is_cached:
                with self.cache_lock:
                    cached_response = self.response_cache.get(f"{currency}:{address}")
                balances[currency] = cached_response.data if cached_response else 0.0
            else:
                result = results[result_idx]
                result_idx += 1
                
                if isinstance(result, Exception):
                    logger.error(f"Ошибка проверки баланса {currency}: {result}")
                    balances[currency] = 0.0
                else:
                    balances[currency] = result
                    # Кэшируем результат
                    with self.cache_lock:
                        self.response_cache[f"{currency}:{address}"] = CachedResponse(
                            result, time.time()
                        )
        
        return balances
    
    async def _check_balance(self, currency: str, address: str) -> float:
        """Проверка баланса для конкретной валюты с ротацией провайдеров"""
        providers = config.API_PROVIDERS.get(currency, [])
        
        for provider_url in providers:
            try:
                url = provider_url.format(address=address)
                result = await self._make_request(url)
                
                if result is not None:
                    balance = self._parse_response(currency, result, provider_url)
                    if balance is not None:
                        self._record_provider_success(provider_url)
                        return balance
            except Exception as e:
                logger.debug(f"Ошибка запроса к {provider_url}: {e}")
                self._record_provider_error(provider_url, str(e))
        
        return 0.0
    
    async def _make_request(self, url: str) -> Optional[str]:
        """Выполнение HTTP запроса с оптимизациями"""
        try:
            async with async_timeout.timeout(config.REQUEST_TIMEOUT):
                async with self.session.get(url) as response:
                    if response.status == 200:
                        content_type = response.headers.get('Content-Type', '')
                        if 'application/json' in content_type:
                            return await response.json()
                        else:
                            return await response.text()
                    elif response.status == 429:  # Rate limit
                        await asyncio.sleep(config.RETRY_DELAY)
                        return None
                    else:
                        return None
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            logger.debug(f"Ошибка выполнения запроса: {e}")
            return None
    
    def _parse_response(self, currency: str, response, provider_url: str) -> float:
        """Парсинг ответа API с оптимизацией"""
        try:
            # Обработка JSON ответов
            if isinstance(response, dict):
                if 'etherscan' in provider_url and response.get('status') == '1':
                    return int(response.get('result', 0)) / 10**18
                elif 'blockcypher' in provider_url:
                    return response.get('balance', 0) / 10**8
                elif 'bscscan' in provider_url and response.get('status') == '1':
                    return int(response.get('result', 0)) / 10**18
            # Обработка текстовых ответов
            elif isinstance(response, str):
                if response.isdigit():
                    return int(response) / 10**8
                elif 'sochain' in provider_url:
                    # Парсинг ответа sochain
                    data = orjson.loads(response)
                    if data.get('status') == 'success':
                        return float(data['data']['confirmed_balance'])
        except Exception as e:
            logger.error(f"Ошибка парсинга ответа: {e}")
        
        return 0.0
    
    def _record_provider_success(self, provider_url: str):
        """Запись успешного запроса"""
        if provider_url not in self.provider_stats:
            self.provider_stats[provider_url] = {'success': 0, 'errors': 0}
        
        self.provider_stats[provider_url]['success'] += 1
    
    def _record_provider_error(self, provider_url: str, error: str):
        """Запись ошибки запроса"""
        if provider_url not in self.provider_stats:
            self.provider_stats[provider_url] = {'success': 0, 'errors': 0}
        
        self.provider_stats[provider_url]['errors'] += 1

# Глобальный экземпляр API клиента
api_client = OptimizedAPIClient()