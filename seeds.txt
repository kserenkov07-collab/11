"""Use Case для поиска адресов."""
import asyncio
from typing import List
from infrastructure.btc_hunter import BTCAPIClient, BTCAddressHunter
from infrastructure.logger import get_logger

logger = get_logger(__name__)


class HuntAddressesUseCase:
    def __init__(self, config: dict):
        self.config = config

    async def execute(self, seeds: List[str], output_file: str):
        async with BTCAPIClient(
            base_delay=self.config.get("base_delay", 2.0),
            max_retries=self.config.get("max_retries", 5),
            timeout=self.config.get("timeout", 30),
            max_reasonable_balance=self.config.get("max_reasonable_balance", 1000.0)
        ) as api:
            hunter = BTCAddressHunter(api, self.config)
            await hunter.run(seeds, output_file)