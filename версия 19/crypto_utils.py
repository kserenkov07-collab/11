"""
Криптографический модуль с оптимизированными функциями.
"""
import os
import hashlib
import base58
import orjson
from typing import Dict, List, Set
from functools import lru_cache
import threading
from config import config
from logger import logger

# Глобальные кэши с блокировками
_CHECKED_MNEMONICS: Set[str] = set()
_CHECKED_MNEMONICS_LOCK = threading.RLock()
_WORDLISTS: Dict[str, List[str]] = {}
_WORDLISTS_LOCK = threading.RLock()

def init_crypto_utils():
    """Инициализация модуля при запуске"""
    load_checked_mnemonics()
    load_wordlists()

def load_checked_mnemonics():
    """Загрузка проверенных мнемонических фраз"""
    global _CHECKED_MNEMONICS
    try:
        if os.path.exists(config.CHECKED_MNEMONICS_FILE):
            # Попробуем разные форматы для обратной совместимости
            try:
                import msgpack
                with open(config.CHECKED_MNEMONICS_FILE, 'rb') as f:
                    _CHECKED_MNEMONICS = set(msgpack.unpackb(f.read()))
                logger.info("Загружены проверенные мнемоники в формате MessagePack")
            except:
                # Попробуем текстовый формат
                with open(config.CHECKED_MNEMONICS_FILE, 'r', encoding='utf-8') as f:
                    _CHECKED_MNEMONICS = set(line.strip() for line in f if line.strip())
                logger.info("Загружены проверенные мнемоники в текстовом формате")
    except Exception as e:
        logger.error(f"Ошибка загрузки проверенных мнемоник: {e}")

def save_checked_mnemonics():
    """Сохранение проверенных мнемонических фраз"""
    try:
        import msgpack
        with _CHECKED_MNEMONICS_LOCK:
            data = list(_CHECKED_MNEMONICS)
        with open(config.CHECKED_MNEMONICS_FILE, 'wb') as f:
            f.write(msgpack.packb(data))
    except Exception as e:
        logger.error(f"Ошибка сохранения проверенных мнемоник: {e}")

def load_wordlists():
    """Загрузка словарей BIP39"""
    global _WORDLISTS
    for lang in config.ENABLED_LANGUAGES:
        try:
            wordlist_file = os.path.join(config.WORDLISTS_DIR, f"{lang}.txt")
            if os.path.exists(wordlist_file):
                with open(wordlist_file, 'r', encoding='utf-8') as f:
                    with _WORDLISTS_LOCK:
                        _WORDLISTS[lang] = [line.strip() for line in f if line.strip()]
                logger.info(f"Загружен словарь {lang}: {len(_WORDLISTS[lang])} слов")
            else:
                logger.warning(f"Словарь {lang} не найден: {wordlist_file}")
        except Exception as e:
            logger.error(f"Ошибка загрузки словаря {lang}: {e}")

def get_wordlist(lang: str) -> List[str]:
    """Получение словаря для указанного языка"""
    with _WORDLISTS_LOCK:
        return _WORDLISTS.get(lang, [])

def generate_mnemonic(lang: str = None) -> str:
    """Генерация мнемонической фразы"""
    if lang is None:
        lang = config.ENABLED_LANGUAGES[0] if config.ENABLED_LANGUAGES else "english"
    
    wordlist = get_wordlist(lang)
    if not wordlist:
        raise ValueError(f"Язык {lang} не поддерживается или словарь пуст")
    
    # Генерируем криптографически безопасную энтропию
    import secrets
    strength_bits = {12: 128, 15: 160, 18: 192, 21: 224, 24: 256}
    strength = strength_bits.get(config.MNEMONIC_LENGTH, 128)
    entropy = secrets.token_bytes(strength // 8)
    
    # Преобразуем энтропию в мнемоническую фразу
    return entropy_to_mnemonic(entropy, wordlist)

def entropy_to_mnemonic(entropy: bytes, wordlist: List[str]) -> str:
    """Преобразование энтропии в мнемоническую фразу"""
    if len(entropy) not in [16, 20, 24, 28, 32]:
        raise ValueError("Длина энтропии должна быть 16, 20, 24, 28 или 32 байта")
    
    # Вычисляем контрольную сумму
    entropy_hash = hashlib.sha256(entropy).digest()
    checksum_bits = bin(int.from_bytes(entropy_hash, 'big'))[2:].zfill(256)[:len(entropy) * 8 // 32]
    
    # Комбинируем энтропию и контрольную сумму
    entropy_bits = bin(int.from_bytes(entropy, 'big'))[2:].zfill(len(entropy) * 8)
    combined_bits = entropy_bits + checksum_bits
    
    # Разделяем на группы по 11 бит
    indices = []
    for i in range(0, len(combined_bits), 11):
        index = int(combined_bits[i:i+11], 2)
        indices.append(index)
    
    # Преобразуем индексы в слова
    return ' '.join([wordlist[i] for i in indices])

@lru_cache(maxsize=10000)
def mnemonic_to_seed(mnemonic: str, passphrase: str = "") -> bytes:
    """Преобразование мнемонической фразы в seed"""
    import hmac
    import hashlib
    
    # Нормализуем мнемоническую фразу и парольную фразу
    mnemonic_normalized = mnemonic.encode('utf-8')
    passphrase_normalized = ("mnemonic" + passphrase).encode('utf-8')
    
    # Используем PBKDF2-HMAC-SHA512
    return hashlib.pbkdf2_hmac(
        'sha512', 
        mnemonic_normalized, 
        passphrase_normalized, 
        2048, 
        64
    )

def derive_eth_address(seed: bytes) -> str:
    """Генерация Ethereum адреса из seed"""
    import ecdsa
    from Crypto.Hash import keccak
    
    # Используем первые 32 байта seed как приватный ключ
    private_key = seed[:32]
    
    # Создаем публичный ключ
    sk = ecdsa.SigningKey.from_string(private_key, curve=ecdsa.SECP256k1)
    vk = sk.get_verifying_key()
    public_key = b'\x04' + vk.to_string()
    
    # Хешируем публичный ключ Keccak-256
    keccak_hash = keccak.new(digest_bits=256)
    keccak_hash.update(public_key)
    address_bytes = keccak_hash.digest()[-20:]
    
    return '0x' + address_bytes.hex()

def derive_btc_address(seed: bytes) -> str:
    """Генерация Bitcoin адреса из seed"""
    import ecdsa
    from Crypto.Hash import RIPEMD160, SHA256
    
    # Используем первые 32 байта seed как приватный ключ
    private_key = seed[:32]
    
    # Создаем публичный ключ
    sk = ecdsa.SigningKey.from_string(private_key, curve=ecdsa.SECP256k1)
    vk = sk.get_verifying_key()
    public_key = b'\x04' + vk.to_string()
    
    # Двойное хеширование SHA-256
    sha256_hash = SHA256.new(public_key).digest()
    ripemd160_hash = RIPEMD160.new(sha256_hash).digest()
    
    # Добавляем префикс сети (0x00 для Bitcoin mainnet)
    network_byte = b'\x00'
    payload = network_byte + ripemd160_hash
    
    # Вычисляем контрольную сумму
    checksum = SHA256.new(SHA256.new(payload).digest()).digest()[:4]
    
    # Кодируем в Base58
    address_bytes = payload + checksum
    return base58.b58encode(address_bytes).decode('ascii')

def derive_addresses(seed: bytes, currencies: List[str] = None) -> Dict[str, str]:
    """Генерация адресов для различных криптовалют"""
    if currencies is None:
        currencies = config.TARGET_CURRENCIES
    
    addresses = {}
    
    for currency in currencies:
        try:
            if currency == "ETH":
                addresses[currency] = derive_eth_address(seed)
            elif currency == "BTC":
                addresses[currency] = derive_btc_address(seed)
            elif currency in ["BSC", "LTC", "XRP", "BCH", "DOGE"]:
                # Для других валют используем аналогичный BTC подход с разными префиксами
                addresses[currency] = derive_btc_like_address(seed, currency)
            else:
                addresses[currency] = ""
        except Exception as e:
            logger.error(f"Ошибка генерации адреса для {currency}: {e}")
            addresses[currency] = ""
    
    return addresses

def derive_btc_like_address(seed: bytes, currency: str) -> str:
    """Генерация BTC-подобного адреса для других криптовалют"""
    import ecdsa
    from Crypto.Hash import RIPEMD160, SHA256
    
    # Соответствие валют и префиксов сетей
    network_prefixes = {
        "BSC": b'\x00',  # Как BTC
        "LTC": b'\x30',  # Префикс для Litecoin
        "BCH": b'\x00',  # Как BTC (legacy)
        "DOGE": b'\x1e', # Префикс для Dogecoin
    }
    
    # Используем префикс сети или по умолчанию как BTC
    network_byte = network_prefixes.get(currency, b'\x00')
    
    # Используем первые 32 байта seed как приватный ключ
    private_key = seed[:32]
    
    # Создаем публичный ключ
    sk = ecdsa.SigningKey.from_string(private_key, curve=ecdsa.SECP256k1)
    vk = sk.get_verifying_key()
    public_key = b'\x04' + vk.to_string()
    
    # Двойное хеширование SHA-256
    sha256_hash = SHA256.new(public_key).digest()
    ripemd160_hash = RIPEMD160.new(sha256_hash).digest()
    
    # Добавляем префикс сети
    payload = network_byte + ripemd160_hash
    
    # Вычисляем контрольную сумму
    checksum = SHA256.new(SHA256.new(payload).digest()).digest()[:4]
    
    # Кодируем в Base58
    address_bytes = payload + checksum
    return base58.b58encode(address_bytes).decode('ascii')

def add_checked_mnemonic(mnemonic: str):
    """Добавление мнемонической фразы в список проверенных"""
    mnemonic_hash = hashlib.sha256(mnemonic.encode('utf-8')).hexdigest()
    
    with _CHECKED_MNEMONICS_LOCK:
        if len(_CHECKED_MNEMONICS) >= config.CACHE_SIZE:
            # Удаляем самые старые записи (FIFO)
            oldest = next(iter(_CHECKED_MNEMONICS))
            _CHECKED_MNEMONICS.remove(oldest)
        
        _CHECKED_MNEMONICS.add(mnemonic_hash)
    
    # Периодически сохраняем на диск
    if len(_CHECKED_MNEMONICS) % 1000 == 0:
        save_checked_mnemonics()

def is_mnemonic_checked(mnemonic: str) -> bool:
    """Проверка, была ли уже проверена мнемоническая фраза"""
    mnemonic_hash = hashlib.sha256(mnemonic.encode('utf-8')).hexdigest()
    
    with _CHECKED_MNEMONICS_LOCK:
        return mnemonic_hash in _CHECKED_MNEMONICS

# Инициализация при импорте
init_crypto_utils()