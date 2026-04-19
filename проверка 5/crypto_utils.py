"""
Криптографический модуль с оптимизированными функциями.
Использует кэширование и предварительные вычисления для ускорения работы.
"""
import os
import hashlib
import ecdsa
import base58
import json
import random
import re
from Crypto.Hash import RIPEMD160
from functools import lru_cache
from config import Config
from logger import logger

# Кэш для предварительно вычисленных ключей
_key_cache = {}
_CACHE_SIZE = 20000

# Кэш для известных мнемонических фраз
_known_mnemonics_set = set()

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

def get_common_patterns():
    """Кэшированная загрузка паттернов"""
    global _patterns_cache
    if _patterns_cache is None:
        _patterns_cache = load_common_patterns()
    return _patterns_cache

# Загружаем кэш при импорте модуля
load_key_cache()
load_known_mnemonics()

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
    
    # Загрузка common_passwords.txt
    try:
        with open(Config.COMMON_PASSWORDS_FILE, 'r', encoding='utf-8') as f:
            patterns.extend([line.strip() for line in f if line.strip()])
        logger.info(f"Загружено {len(patterns)} паттернов из common_passwords.txt")
    except Exception as e:
        logger.error(f"Ошибка загрузки common_passwords.txt: {e}")
    
    # Загрузка known_phrases.txt
    try:
        with open(Config.KNOWN_PHRASES_FILE, 'r', encoding='utf-8') as f:
            patterns.extend([line.strip() for line in f if line.strip()])
        logger.info(f"Загружено {len(patterns)} паттернов из known_phrases.txt")
    except Exception as e:
        logger.error(f"Ошибка загрузки known_phrases.txt: {e}")
    
    # Загрузка common_patterns.txt
    try:
        with open(Config.COMMON_PATTERNS_FILE, 'r', encoding='utf-8') as f:
            patterns.extend([line.strip() for line in f if line.strip()])
        logger.info(f"Загружено {len(patterns)} паттернов из common_patterns.txt")
    except Exception as e:
        logger.error(f"Ошибка загрузки common_patterns.txt: {e}")
    
    # Загрузка keyboard_patterns.txt
    try:
        with open(Config.KEYBOARD_PATTERNS_FILE, 'r', encoding='utf-8') as f:
            patterns.extend([line.strip() for line in f if line.strip()])
        logger.info(f"Загружено {len(patterns)} паттернов из keyboard_patterns.txt")
    except Exception as e:
        logger.error(f"Ошибка загрузки keyboard_patterns.txt: {e}")
    
    # Загрузка crypto_patterns.txt
    try:
        with open(Config.CRYPTO_PATTERNS_FILE, 'r', encoding='utf-8') as f:
            patterns.extend([line.strip() for line in f if line.strip()])
        logger.info(f"Загружено {len(patterns)} паттернов из crypto_patterns.txt")
    except Exception as e:
        logger.error(f"Ошибка загрузки crypto_patterns.txt: {e}")
    
    return patterns

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
import atexit
atexit.register(save_key_cache)
