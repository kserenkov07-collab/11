"""
Инструменты для ручной проверки мнемонических фраз.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))  # Исправлено: убрана лишняя скобка

from crypto_utils import mnemonic_to_seed, derive_eth_address, derive_btc_address
from api_client import check_balances_batch_async
from config import Config
from logger import logger

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
