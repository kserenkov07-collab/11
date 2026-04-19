"""
Криптографический модуль с оптимизированными функции.
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

# Кэш для предварительно вычисленных ключей
_key_cache = {}
_CACHE_SIZE = 10000  # Размер кэша

def save_key_cache():
    """Сохранение кэша ключей на диск"""
    if not Config.USE_PERSISTENT_CACHE:
        return
    
    cache_file = os.path.join(Config.CACHE_DIR, "key_cache.json")
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(_key_cache, f, indent=2)
    except:
        pass

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
    except:
        _key_cache = {}

# Загружаем кэш при импорте модуля
load_key_cache()

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

def load_common_patterns():
    """Загрузка распространенных паттернов из файлов"""
    patterns = []
    
    # Загрузка common_passwords.txt
    try:
        with open(Config.COMMON_PASSWORDS_FILE, 'r', encoding='utf-8') as f:
            patterns.extend([line.strip() for line in f if line.strip()])
    except:
        pass
    
    # Загрузка known_phrases.txt
    try:
        with open(Config.KNOWN_PHRASES_FILE, 'r', encoding='utf-8') as f:
            patterns.extend([line.strip() for line in f if line.strip()])
    except:
        pass
    
    # Загрузка common_patterns.txt
    try:
        with open(Config.COMMON_PATTERNS_FILE, 'r', encoding='utf-8') as f:
            patterns.extend([line.strip() for line in f if line.strip()])
    except:
        pass
    
    # Загрузка keyboard_patterns.txt
    try:
        with open(Config.KEYBOARD_PATTERNS_FILE, 'r', encoding='utf-8') as f:
            patterns.extend([line.strip() for line in f if line.strip()])
    except:
        pass
    
    return patterns

def generate_human_mnemonic(wordlist, length=12, pattern_type=None):
    """Генерация мнемонических фраз BIP-39 с уникальными словами"""
    # Всегда гарантируем уникальность слов
    if not Config.USE_HUMAN_PATTERNS:
        # Случайная генерация без повторений (правильная BIP-39)
        return ' '.join(random.sample(wordlist, length))
    
    common_patterns = load_common_patterns()
    
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
        
        return ' '.join(unique_words)
    
    # Случайная генерация без повторений (правильная BIP-39)
    return ' '.join(random.sample(wordlist, length))

def heuristic_score(address, tx_activity=None, balance_data=None):
    """Оценка вероятности, что адрес создан человеком"""
    score = 0
    
    # Проверка на наличие паттернов (повторяющиеся символы)
    for i in range(len(address) - 3):
        if address[i] == address[i+1] == address[i+2]:
            score += 10
    
    # Проверка на простые последовательности
    simple_seqs = ["123", "abc", "000", "111", "222", "333", "444", "555", "666", "777", "888", "999"]
    for seq in simple_seqs:
        if seq in address.lower():
            score += 15
    
    # Проверка на короткие адреса (vanity addresses)
    if len(set(address)) < 10:
        score += 20
    
    # Проверка активности кошелька
    if tx_activity and Config.USE_TX_ACTIVITY_CHECK:
        for currency, tx_count in tx_activity.items():
            if tx_count > Config.MIN_TX_COUNT:
                score += 25  # Активный кошелек
    
    # Проверка баланса
    if balance_data and balance_data['total_usd'] > Config.MIN_TOTAL_BALANCE_USD * 10:
        score += 30  # Значительный баланс
    
    # Проверка на соответствие формату (только для ETH)
    if address.startswith('0x'):
        if re.match(r'^0x[a-fA-F0-9]{40}$', address):
            score += 5  # Корректный формат ETH адреса
    
    return score

# Сохраняем кэш при выходе
import atexit
atexit.register(save_key_cache)
