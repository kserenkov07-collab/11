import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from infrastructure.logger import get_logger
from infrastructure.bip39_generator import UniqueWordsGenerator
from infrastructure.bip_derivator import SingleStandardDerivator
from infrastructure.checkpoint import Checkpoint
from application.scan_targets import ScanTargetsUseCase
from presentation.cli import (
    load_targets, group_by_standard,
    InMemoryTargetRepository, ConsoleResultSaver
)

logger = get_logger(__name__)

# ================== НАСТРОЙКИ (ИЗМЕНЯЙТЕ ЗДЕСЬ) ==================
TARGETS_FILE = "data/targets.txt"
WORKERS = 2                     # 2 воркера → ~50% CPU, 1 → ~25%
ADDRESS_LIMIT = 20
CHECK_CHANGE = True
STOP_AFTER_FIRST = False
CHECKPOINT_INTERVAL = 5000
SEED = None                     # None = случайное зерно
REQUIRE_UNIQUE = True
# =================================================================

# Попытка снизить приоритет процесса (требуется psutil)
try:
    import psutil
    p = psutil.Process()
    if os.name == 'nt':
        p.nice(psutil.IDLE_PRIORITY_CLASS)
    else:
        p.nice(10)
    logger.info("Process priority lowered")
except ImportError:
    logger.info("psutil not installed – priority unchanged")
except Exception as e:
    logger.debug(f"Priority change failed: {e}")

def main():
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
            derivator_class=SingleStandardDerivator,
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

if __name__ == "__main__":
    main()
