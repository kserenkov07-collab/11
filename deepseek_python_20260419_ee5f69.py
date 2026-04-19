import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from infrastructure.logger import get_logger
from application.hunt_addresses import HuntAddressesUseCase
from presentation.cli import load_seeds

logger = get_logger(__name__)

SEEDS_FILE = "data/seeds.txt"
TARGETS_FILE = "data/targets.txt"
CONFIG = {
    "max_depth": 5,
    "min_balance": 0.001,
    "inactive_days": 365,
    "max_addresses": 10000,
    "base_delay": 2.0,
    "checkpoint_interval": 10,
}

async def main():
    seeds = load_seeds(SEEDS_FILE)
    if not seeds:
        logger.error(f"No seed addresses found in {SEEDS_FILE}")
        return
    use_case = HuntAddressesUseCase(CONFIG)
    await use_case.execute(seeds, TARGETS_FILE)

if __name__ == "__main__":
    asyncio.run(main())