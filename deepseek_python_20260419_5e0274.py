import concurrent.futures
import time
import gc
from typing import List, Optional, Set, Tuple, FrozenSet
from domain.entities import Mnemonic, Address, ScanResult
from domain.interfaces import MnemonicGenerator, AddressDerivator, TargetRepository, ResultSaver
from infrastructure.logger import get_logger
from infrastructure.platform_guesser import guess_platform

logger = get_logger(__name__)

_worker_derivator = None
_worker_address_limit = None

def _init_worker(derivator_class, standard, check_change, address_limit):
    global _worker_derivator, _worker_address_limit
    _worker_derivator = derivator_class(standard, check_change)
    _worker_address_limit = address_limit
    gc.disable()

def _check_candidate_worker(mnemonic: Mnemonic, remaining_set: FrozenSet[str]) -> Optional[Tuple]:
    global _worker_derivator, _worker_address_limit
    try:
        derived, seed_hex = _worker_derivator.derive(mnemonic, _worker_address_limit)
    except Exception:
        return None
    for standard, path, address in derived:
        if address.value in remaining_set:
            platform = guess_platform(standard, path, address.value)
            return (mnemonic, address, standard, path, platform, seed_hex)
    return None

class ScanTargetsUseCase:
    def __init__(self, generator: MnemonicGenerator, derivator_class, standard: str,
                 target_repo: TargetRepository, result_saver: ResultSaver,
                 max_workers: int = 4, address_limit: int = 20,
                 stop_after_first: bool = False, checkpoint_interval: int = 5000,
                 check_change: bool = True):
        self.generator = generator
        self.derivator_class = derivator_class
        self.standard = standard
        self.check_change = check_change
        self.target_repo = target_repo
        self.result_saver = result_saver
        self.max_workers = max_workers
        self.address_limit = address_limit
        self.stop_after_first = stop_after_first
        self.checkpoint_interval = checkpoint_interval
        self._checked = 0
        self._stop_requested = False

    def _on_match_found(self, result: ScanResult):
        self.target_repo.mark_found(result.address)
        self.result_saver.save(result)
        logger.critical("\n" + "="*80)
        logger.critical(f"🎯 MATCH FOUND! Address: {result.address.value}")
        logger.critical(f"Platform: {result.platform}")
        logger.critical(f"Standard: {result.standard} ({result.derivation_path})")
        logger.critical(f"Mnemonic: {result.mnemonic.phrase}")
        logger.critical("="*80 + "\n")
        if self.stop_after_first or not self.target_repo.get_remaining():
            self._stop_requested = True

    def execute(self) -> List[ScanResult]:
        logger.info(f"Starting scan for {self.standard} with {self.max_workers} workers")
        logger.info(f"Remaining targets: {len(self.target_repo.get_remaining())}")
        start_time = time.time()
        found_results = []
        last_checkpoint = getattr(self.generator, 'counter', 0)
        remaining_frozen = frozenset(addr.value for addr in self.target_repo.get_remaining())

        with concurrent.futures.ProcessPoolExecutor(
            max_workers=self.max_workers,
            initializer=_init_worker,
            initargs=(self.derivator_class, self.standard, self.check_change, self.address_limit)
        ) as executor:
            batch_size = self.max_workers * 200
            futures = set()
            gen = self.generator.generate()

            while not self._stop_requested and self.target_repo.get_remaining():
                current_remaining = self.target_repo.get_remaining()
                if len(current_remaining) != len(remaining_frozen):
                    remaining_frozen = frozenset(addr.value for addr in current_remaining)

                while len(futures) < batch_size and not self._stop_requested:
                    try:
                        mnemonic = next(gen)
                    except StopIteration:
                        break
                    futures.add(executor.submit(_check_candidate_worker, mnemonic, remaining_frozen))

                if not futures:
                    break

                done, futures = concurrent.futures.wait(
                    futures, timeout=0.1, return_when=concurrent.futures.FIRST_COMPLETED
                )

                for future in done:
                    worker_result = future.result()
                    self._checked += 1
                    if worker_result:
                        mnemonic, address, standard, path, platform, seed_hex = worker_result
                        result = ScanResult(
                            mnemonic=mnemonic,
                            address=address,
                            standard=standard,
                            derivation_path=path,
                            platform=platform,
                            seed_hex=seed_hex
                        )
                        found_results.append(result)
                        self._on_match_found(result)
                        if self._stop_requested:
                            executor.shutdown(wait=False, cancel_futures=True)
                            break

                if hasattr(self.generator, 'counter'):
                    if self.generator.counter - last_checkpoint >= self.checkpoint_interval:
                        self.generator.save_state()
                        last_checkpoint = self.generator.counter

                if self._checked % 5000 == 0:
                    elapsed = time.time() - start_time
                    rate = self._checked / elapsed if elapsed > 0 else 0
                    logger.info(f"Checked: {self._checked} | Rate: {rate:.1f}/s | Remaining: {len(self.target_repo.get_remaining())}")

                time.sleep(0.01)  # небольшая пауза для снижения нагрузки

        self.generator.save_state()
        elapsed = time.time() - start_time
        logger.info(f"Scan finished in {elapsed:.1f}s. Checked {self._checked} mnemonics.")
        return found_results