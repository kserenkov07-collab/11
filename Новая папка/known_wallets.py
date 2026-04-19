"""
Модуль для работы с базой данных известных кошельков.
"""
import sqlite3
import os
import time
from config import Config

class KnownWalletsDB:
    """База данных известных кошельков"""
    
    def __init__(self, db_path=Config.KNOWN_WALLETS_DB):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Оптимизированная инициализация базы данных"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Включаем журналирование WAL для лучшей производительности
        c.execute("PRAGMA journal_mode=WAL")
        
        # Увеличиваем размер кэша
        c.execute(f"PRAGMA cache_size=-{Config.DB_CACHE_SIZE}")
        
        # Создаем таблицу для известных кошельков
        c.execute('''CREATE TABLE IF NOT EXISTS wallets
                     (address TEXT PRIMARY KEY, 
                      balance_usd REAL,
                      tx_count INTEGER,
                      last_active INTEGER,
                      created_at INTEGER)''')
        
        # Создаем индексы для ускорения поиска
        c.execute('''CREATE INDEX IF NOT EXISTS idx_balance_usd ON wallets(balance_usd)''')
        c.execute('''CREATE INDEX IF NOT EXISTS idx_tx_count ON wallets(tx_count)''')
        c.execute('''CREATE INDEX IF NOT EXISTS idx_last_active ON wallets(last_active)''')
        
        conn.commit()
        conn.close()
    
    def add_wallet(self, address, balance_usd=0, tx_count=0, last_active=0):
        """Добавление кошелька в базу данных"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("INSERT OR REPLACE INTO wallets VALUES (?, ?, ?, ?, ?)",
                  (address, balance_usd, tx_count, last_active, int(time.time())))
        
        conn.commit()
        conn.close()
    
    def add_wallets_batch(self, wallets):
        """Пакетное добавление кошельков"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        current_time = int(time.time())
        data = [(address, balance_usd, tx_count, last_active, current_time) 
                for address, balance_usd, tx_count, last_active in wallets]
        
        c.executemany("INSERT OR REPLACE INTO wallets VALUES (?, ?, ?, ?, ?)", data)
        
        conn.commit()
        conn.close()
    
    def is_known(self, address):
        """Проверка, известен ли кошелек"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("SELECT * FROM wallets WHERE address=?", (address,))
        result = c.fetchone()
        
        conn.close()
        return result is not None
    
    def are_known_batch(self, addresses):
        """Пакетная проверка, известны ли кошельки"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        placeholders = ','.join(['?' for _ in addresses])
        query = f"SELECT address FROM wallets WHERE address IN ({placeholders})"
        
        c.execute(query, addresses)
        known_addresses = {row[0] for row in c.fetchall()}
        
        conn.close()
        return {addr: addr in known_addresses for addr in addresses}
    
    def get_active_wallets(self, min_balance_usd=0, min_tx=1, max_inactive_days=365):
        """Получение активных кошельков"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        max_inactive_seconds = max_inactive_days * 24 * 60 * 60
        current_time = int(time.time())
        
        c.execute("SELECT * FROM wallets WHERE balance_usd>=? AND tx_count>=? AND last_active>=?", 
                  (min_balance_usd, min_tx, current_time - max_inactive_seconds))
        result = c.fetchall()
        
        conn.close()
        return result
    
    def import_from_file(self, file_path, wallet_type="eth"):
        """Импорт кошельков из файла"""
        imported = 0
        try:
            with open(file_path, 'r') as f:
                wallets = []
                for line in f:
                    address = line.strip()
                    if address:
                        wallets.append((address, 0, 0, 0))
                        imported += 1
                        # Пакетно добавляем каждые 1000 кошельков
                        if len(wallets) >= 1000:
                            self.add_wallets_batch(wallets)
                            wallets = []
                
                # Добавляем оставшиеся кошельки
                if wallets:
                    self.add_wallets_batch(wallets)
            
            return imported
        except Exception as e:
            print(f"Ошибка импорта из файла {file_path}: {e}")
            return imported

# Глобальный экземпляр базы данных
known_wallets_db = KnownWalletsDB()