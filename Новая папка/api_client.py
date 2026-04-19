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
from config import Config
from async_manager import async_manager, async_command

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
            if current_time - cached_time < Config.CACHE_EXPIRY:
                results[cache_key] = balance
                continue
    
    # Формируем URL для запросов, которые не в кэше
    urls_to_fetch = []
    keys_to_fetch = []
    
    for currency, address in currency_address_pairs:
        cache_key = f"{currency}_{address}"
        if cache_key not in results:
            if currency in Config.CRYPTOCURRENCIES:
                url = Config.CRYPTOCURRENCIES[currency]["api_url"].format(address)
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
                    if currency == "BTC":
                        balance = int(response) / 10**8
                    elif currency in ["ETH", "BNB"]:
                        data = json.loads(response)
                        balance = int(data.get('result', 0)) / 10**18 if data.get('status') == '1' else 0
                    elif currency in ["USDT_ETH", "USDT_BSC"]:
                        data = json.loads(response)
                        balance = int(data.get('result', 0)) / 10**6 if data.get('status') == '1' else 0
                    elif currency == "USDT_TRON":
                        data = json.loads(response)
                        if data.get('data') and len(data['data']) > 0:
                            trc20 = data['data'][0].get('trc20', [])
                            for token in trc20:
                                if 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t' in token:
                                    balance = token['TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t'] / 10**6
                                    break
                except:
                    balance = 0
            
            results[cache_key] = balance
            request_cache[cache_key] = (current_time, balance)
    
    return results

async def get_exchange_rates(session):
    """Получение актуальных курсов криптовалют к USD"""
    global exchange_rates
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,tether,binancecoin&vs_currencies=usd"
        async with session.get(url, timeout=10) as response:
            if response.status == 200:
                data = await response.json()
                exchange_rates = {
                    'BTC': data.get('bitcoin', {}).get('usd', 0),
                    'ETH': data.get('ethereum', {}).get('usd', 0),
                    'USDT': data.get('tether', {}).get('usd', 1),
                    'BNB': data.get('binancecoin', {}).get('usd', 0)
                }
    except Exception:
        # Используем значения по умолчанию в случае ошибки
        exchange_rates = {
            'BTC': 50000,
            'ETH': 3000,
            'USDT': 1,
            'BNB': 400
        }

async def get_balance_async(session, currency, address):
    """Асинхронное получение баланса для конкретной валюты"""
    cache_key = f"{currency}_{address}"
    current_time = time.time()
    
    if cache_key in request_cache:
        cached_time, balance = request_cache[cache_key]
        if current_time - cached_time < Config.CACHE_EXPIRY:
            return balance
    
    try:
        balance = 0
        
        if currency == "BTC":
            response = await make_async_request(session, Config.CRYPTOCURRENCIES[currency]["api_url"].format(address))
            if response:
                balance = int(response) / 10**8
            elif "api_url_backup" in Config.CRYPTOCURRENCIES[currency]:
                response = await make_async_request(session, Config.CRYPTOCURRENCIES[currency]["api_url_backup"].format(address))
                if response:
                    data = json.loads(response)
                    balance = data.get('balance', 0) / 10**8
        
        elif currency in ["ETH", "BNB"]:
            response = await make_async_request(session, Config.CRYPTOCURRENCIES[currency]["api_url"].format(address))
            if response:
                data = json.loads(response)
                balance = int(data.get('result', 0)) / 10**18 if data.get('status') == '1' else 0
            elif "api_url_backup" in Config.CRYPTOCURRENCIES[currency]:
                response = await make_async_request(session, Config.CRYPTOCURRENCIES[currency]["api_url_backup"].format(address))
                if response:
                    data = json.loads(response)
                    balance = data.get('balance', 0) / 10**18
        
        elif currency in ["USDT_ETH", "USDT_BSC"]:
            response = await make_async_request(session, Config.CRYPTOCURRENCIES[currency]["api_url"].format(address))
            if response:
                data = json.loads(response)
                balance = int(data.get('result', 0)) / 10**6 if data.get('status') == '1' else 0
        
        elif currency == "USDT_TRON":
            response = await make_async_request(session, Config.CRYPTOCURRENCIES[currency]["api_url"].format(address))
            if response:
                data = json.loads(response)
                if data.get('data') and len(data['data']) > 0:
                    trc20 = data['data'][0].get('trc20', [])
                    for token in trc20:
                        if 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t' in token:
                            balance = token['TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t'] / 10**6
                            break
            
        request_cache[cache_key] = (current_time, balance)
        return balance
    except Exception:
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
    except Exception:
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
            if currency in ["ETH", "USDT_ETH", "USDT_TRON", "BNB", "USDT_BSC"]:
                address = addresses["eth"]
            else:
                address = addresses["btc"]
            
            currency_address_pairs.append((currency, address))
        
        # Используем пакетную обработку, если включена
        if Config.USE_BATCH_API:
            balance_results_dict = await get_balances_batch_async(session, currency_address_pairs)
            
            # Преобразуем результаты в формат, совместимый с остальным кодом
            for i, currency in enumerate(Config.TARGET_CURRENCIES):
                if currency in ["ETH", "USDT_ETH", "USDT_TRON", "BNB", "USDT_BSC"]:
                    address = addresses["eth"]
                else:
                    address = addresses["btc"]
                
                cache_key = f"{currency}_{address}"
                balances[currency] = balance_results_dict.get(cache_key, 0)
        else:
            # Старый метод для обратной совместимости
            balance_tasks = []
            for currency in Config.TARGET_CURRENCIES:
                if currency in ["ETH", "USDT_ETH", "USDT_TRON", "BNB", "USDT_BSC"]:
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
                    if currency in ["ETH", "USDT_ETH", "USDT_TRON", "BNB", "USDT_BSC"]:
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
        except Exception:
            pass

atexit.register(save_api_cache)