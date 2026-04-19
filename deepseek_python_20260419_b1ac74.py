import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from infrastructure.logger import get_logger
from application.hunt_addresses import HuntAddressesUseCase
from presentation.cli import load_seeds, load_targets, group_by_standard
from infrastructure.bip39_generator import UniqueWordsGenerator
from infrastructure.coincurve_derivator import CoinCurveDerivator
from infrastructure.checkpoint import Checkpoint
from application.scan_targets import ScanTargetsUseCase
from presentation.cli import InMemoryTargetRepository, ConsoleResultSaver

logger = get_logger(__name__)

SEEDS_FILE = "data/seeds.txt"
TARGETS_FILE = "data/targets.txt"
HUNT_CONFIG = {
    "max_depth": 5,
    "min_balance": 0.001,
    "inactive_days": 365,
    "max_addresses": 10000,
    "base_delay": 2.0,
    "checkpoint_interval": 10,
}

WORKERS = 4
ADDRESS_LIMIT = 20
CHECK_CHANGE = True
STOP_AFTER_FIRST = False
CHECKPOINT_INTERVAL = 5000
SEED = None
REQUIRE_UNIQUE = False

async def run_hunt():
    seeds = load_seeds(SEEDS_FILE)
    if not seeds:
        logger.error(f"No seed addresses found in {SEEDS_FILE}")
        return
    use_case = HuntAddressesUseCase(HUNT_CONFIG)
    await use_case.execute(seeds, TARGETS_FILE)

def run_crack():
    targets = load_targets(TARGETS_FILE)
    if not targets:
        logger.error(f"No target addresses found in {TARGETS_FILE}")
        return
    logger.info(f"Loaded {len(targets)} target addresses")
    groups = group_by_standard(targets)
    all_results = []
    for standard, addresses in groups.items():
        if not addresses:
            continue
        logger.info(f"=== Processing {standard} group with {len(addresses)} addresses ===")
        checkpoint = Checkpoint(f'data/checkpoints/{standard}.json')
        target_repo = InMemoryTargetRepository(addresses)
        saver = ConsoleResultSaver()
        generator = UniqueWordsGenerator(
            mode='counter',
            seed=SEED,
            checkpoint=checkpoint,
            require_unique=REQUIRE_UNIQUE
        )
        use_case = ScanTargetsUseCase(
            generator=generator,
            derivator_class=CoinCurveDerivator,
            standard=standard,
            target_repo=target_repo,
            result_saver=saver,
            max_workers=WORKERS,
            address_limit=ADDRESS_LIMIT,
            stop_after_first=STOP_AFTER_FIRST,
            checkpoint_interval=CHECKPOINT_INTERVAL,
            check_change=CHECK_CHANGE
        )
        results = use_case.execute()
        all_results.extend(results)
        if STOP_AFTER_FIRST and results:
            break
    if all_results:
        print("\nAll found wallets:")
        for r in all_results:
            print(f"{r.address.value} -> {r.platform} : {r.mnemonic.phrase}")
    else:
        print("No matches found.")

async def main():
    await run_hunt()
    run_crack()

if __name__ == "__main__":
    asyncio.run(main())