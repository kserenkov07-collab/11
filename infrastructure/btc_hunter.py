"""Асинхронный BFS-обход транзакций через mempool.space."""
import asyncio
import aiohttp
import hashlib
import json
import os
import pickle
import random
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple

from infrastructure.logger import get_logger

logger = get_logger(__name__)

CACHE_DIR = "data/hunter_cache"
STATE_DIR = "data/hunter_state"
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(STATE_DIR, exist_ok=True)


class FileCache:
    def __init__(self, ttl_hours: int = 24):
        self.ttl = timedelta(hours=ttl_hours)

    def _key(self, address: str) -> str:
        return hashlib.md5(f"btc:{address}".encode()).hexdigest()

    def get(self, address: str) -> Optional[Dict]:
        path = os.path.join(CACHE_DIR, self._key(address) + ".json")
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cache_time = datetime.fromisoformat(data.get("cache_time", "2000-01-01"))
            if datetime.now() - cache_time < self.ttl:
                return data.get("data")
        except Exception:
            pass
        return None

    def set(self, address: str, info: Dict):
        path = os.path.join(CACHE_DIR, self._key(address) + ".json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({
                    "address": address,
                    "data": info,
                    "cache_time": datetime.now().isoformat()
                }, f)
        except Exception as e:
            logger.debug(f"Cache write failed: {e}")


class BTCAPIClient:
    def __init__(self, base_delay: float = 2.0, max_retries: int = 5,
                 timeout: int = 30, max_reasonable_balance: float = 1000.0):
        self.base_delay = base_delay
        self.max_retries = max_retries
        self.timeout = timeout
        self.max_reasonable = max_reasonable_balance
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_req = 0.0
        self.current_delay = base_delay
        self.cache = FileCache()

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()

    async def _request(self, url: str) -> Optional[dict]:
        for attempt in range(self.max_retries):
            jitter = random.uniform(0.5, 1.5)
            wait = self.current_delay + jitter
            now = time.time()
            if now - self.last_req < wait:
                await asyncio.sleep(wait - (now - self.last_req))
            self.last_req = time.time()
            try:
                async with self.session.get(url, timeout=self.timeout) as resp:
                    if resp.status == 200:
                        self.current_delay = max(self.base_delay, self.current_delay * 0.9)
                        return await resp.json()
                    if resp.status == 429:
                        self.current_delay = min(60, self.current_delay * 2)
                        await asyncio.sleep(self.current_delay)
                    else:
                        logger.debug(f"HTTP {resp.status} for {url[:80]}")
                        return None
            except asyncio.TimeoutError:
                logger.debug(f"Timeout {url[:60]}")
            except Exception as e:
                logger.debug(f"Request error: {e}")
            await asyncio.sleep(2 ** attempt)
        return None

    async def get_address_info(self, address: str) -> Optional[Dict]:
        cached = self.cache.get(address)
        if cached:
            return cached

        url = f"https://mempool.space/api/address/{address}"
        data = await self._request(url)
        if not data or not isinstance(data, dict):
            return None

        chain_stats = data.get("chain_stats")
        if not isinstance(chain_stats, dict):
            info = {"balance": 0.0, "last_tx_time": None, "related": []}
            self.cache.set(address, info)
            return info

        funded = chain_stats.get("funded_txo_sum", 0)
        spent = chain_stats.get("spent_txo_sum", 0)
        balance = (funded - spent) / 1e8
        if balance > self.max_reasonable:
            return None
        if balance > 0 and chain_stats.get("tx_count", 0) == 0:
            return None

        txs_url = f"https://mempool.space/api/address/{address}/txs"
        txs_data = await self._request(txs_url)
        last_tx_time = None
        related = set()
        if txs_data and isinstance(txs_data, list):
            for tx in txs_data[:50]:
                if not last_tx_time:
                    last_tx_time = tx.get("status", {}).get("block_time")
                for inp in tx.get("vin", []):
                    a = inp.get("prevout", {}).get("scriptpubkey_address")
                    if a and a != address:
                        related.add(a)
                for out in tx.get("vout", []):
                    a = out.get("scriptpubkey_address")
                    if a and a != address:
                        related.add(a)
                if len(related) > 50:
                    break

        info = {"balance": balance, "last_tx_time": last_tx_time,
                "related": list(related)[:30]}
        self.cache.set(address, info)
        return info


class BTCAddressHunter:
    """BFS-обход для поиска неактивных адресов с балансом."""

    def __init__(self, api: BTCAPIClient, config: dict):
        self.api = api
        self.max_depth = config.get("max_depth", 5)
        self.min_balance = config.get("min_balance", 0.001)
        self.inactive_days = config.get("inactive_days", 365)
        self.max_addresses = config.get("max_addresses", 10000)
        self.checkpoint_interval = config.get("checkpoint_interval", 10)
        self.visited: Set[str] = set()
        self.queue: deque = deque()
        self.processed = 0
        self.found = set()
        self._stop = False

    def _save_state(self):
        with open(os.path.join(STATE_DIR, "visited.pkl"), "wb") as f:
            pickle.dump(self.visited, f)
        with open(os.path.join(STATE_DIR, "queue.pkl"), "wb") as f:
            pickle.dump(list(self.queue), f)
        logger.info(f"State saved: {len(self.visited)} visited, {len(self.queue)} queued")

    def _load_state(self):
        vp = os.path.join(STATE_DIR, "visited.pkl")
        qp = os.path.join(STATE_DIR, "queue.pkl")
        if os.path.exists(vp):
            with open(vp, "rb") as f:
                self.visited = pickle.load(f)
        if os.path.exists(qp):
            with open(qp, "rb") as f:
                self.queue = deque(pickle.load(f))
        self.processed = len(self.visited)

    def _days_inactive(self, ts: Optional[int]) -> Optional[int]:
        return None if ts is None else (int(time.time()) - ts) // 86400

    async def run(self, seeds: List[str], output_file: str):
        self._load_state()
        if not self.queue:
            for addr in seeds:
                if addr not in self.visited:
                    self.visited.add(addr)
                    self.queue.append((addr, 0))
            self._save_state()

        logger.info(f"BFS start: depth={self.max_depth}, queue={len(self.queue)}")
        start_time = time.time()
        last_checkpoint = self.processed

        while self.queue and self.processed < self.max_addresses and not self._stop:
            if self.processed - last_checkpoint >= self.checkpoint_interval:
                self._save_state()
                last_checkpoint = self.processed

            if len(self.queue) > 5000:
                while len(self.queue) > 2500:
                    self.queue.pop()

            addr, depth = self.queue.popleft()
            self.processed += 1

            if depth > self.max_depth:
                continue

            info = await self.api.get_address_info(addr)
            if not info:
                continue

            balance = info["balance"]
            last_tx = info.get("last_tx_time")
            days = self._days_inactive(last_tx)
            dormant = (days is None) or (days >= self.inactive_days)

            if balance >= self.min_balance and dormant and addr not in self.found:
                self.found.add(addr)
                logger.info(f"💰 FOUND: {addr[:20]}... balance={balance:.8f} BTC, inactive={days} days")
                with open(output_file, "a", encoding="utf-8") as f:
                    f.write(addr + "\n")

            if depth < self.max_depth:
                for rel in info.get("related", [])[:30]:
                    if rel not in self.visited:
                        self.visited.add(rel)
                        self.queue.append((rel, depth + 1))

            if self.processed % 20 == 0:
                elapsed = time.time() - start_time
                rate = self.processed / elapsed if elapsed > 0 else 0
                print(f"[Hunt] processed {self.processed}, queue {len(self.queue)}, "
                      f"found {len(self.found)}, rate {rate:.1f}/s")

        self._save_state()
        logger.info(f"Hunt finished. Processed {self.processed}, found {len(self.found)}")