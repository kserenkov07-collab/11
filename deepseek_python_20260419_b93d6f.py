import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from presentation.cli import parse_arguments, load_targets, load_seeds, group_by_standard
from presentation.cli import InMemoryTargetRepository, ConsoleResultSaver
from infrastructure.logger import get_logger
from infrastructure.checkpoint import Checkpoint
from infrastructure.bip39_generator import UniqueWordsGenerator
from infrastructure.coincurve_derivator import CoinCurveDerivator
from application.scan_targets import ScanTargetsUseCase
from application.hunt_addresses import HuntAddressesUseCase

logger = get_logger(__name__)

async def run_hunt(args):
    seeds = load_seeds(args.seeds)
    if not seeds:
        logger.error(f"No seed addresses found in {args.seeds}")
        return
    config = {
        "max_depth": args.max_depth,
        "min_balance": args.min_balance,
        "inactive_days": args.inactive_days,
        "max_addresses": args.max_addresses,
        "base_delay": args.base_delay,
        "checkpoint_interval": 10,
    }
    use_case = HuntAddressesUseCase(config)
    await use_case.execute(seeds, args.targets)

def run_crack(args):
    targets = load_targets(args.targets)
    if not targets:
        logger.error(f"No target addresses found in {args.targets}")
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
            seed=args.seed,
            checkpoint=checkpoint,
            require_unique=args.require_unique
        )
        use_case = ScanTargetsUseCase(
            generator=generator,
            derivator_class=CoinCurveDerivator,
            standard=standard,
            target_repo=target_repo,
            result_saver=saver,
            max_workers=args.workers,
            address_limit=args.address_limit,
            stop_after_first=args.stop_after_first,
            checkpoint_interval=args.checkpoint_interval,
            check_change=not args.no_change
        )
        results = use_case.execute()
        all_results.extend(results)
        if args.stop_after_first and results:
            break
    if all_results:
        print("\nAll found wallets:")
        for r in all_results:
            print(f"{r.address.value} -> {r.platform} : {r.mnemonic.phrase}")
    else:
        print("No matches found.")

async def run_full(args):
    await run_hunt(args)
    run_crack(args)

def main():
    args = parse_arguments()
    if args.mode == 'hunt':
        asyncio.run(run_hunt(args))
    elif args.mode == 'crack':
        run_crack(args)
    else:  # full
        asyncio.run(run_full(args))

if __name__ == "__main__":
    main()