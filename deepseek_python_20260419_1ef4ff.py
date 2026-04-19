import argparse
from typing import Dict, Set, List
from domain.entities import Address
from infrastructure.platform_guesser import get_standard_from_address

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Meta Hunter – CTF Full Cycle Tool')
    parser.add_argument('--mode', choices=['hunt', 'crack', 'full'], default='full')
    parser.add_argument('--targets', default='data/targets.txt')
    parser.add_argument('--seeds', default='data/seeds.txt')
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--max-depth', type=int, default=5)
    parser.add_argument('--min-balance', type=float, default=0.001)
    parser.add_argument('--inactive-days', type=int, default=365)
    parser.add_argument('--max-addresses', type=int, default=10000)
    parser.add_argument('--base-delay', type=float, default=2.0)
    parser.add_argument('--address-limit', type=int, default=20)
    parser.add_argument('--no-change', action='store_true')
    parser.add_argument('--stop-after-first', action='store_true')
    parser.add_argument('--seed', type=int)
    parser.add_argument('--checkpoint-interval', type=int, default=5000)
    parser.add_argument('--require-unique', action='store_true')
    return parser.parse_args()

def load_targets(filepath: str) -> Set[Address]:
    try:
        with open(filepath, 'r') as f:
            return {Address(line.strip()) for line in f if line.strip()}
    except FileNotFoundError:
        return set()

def load_seeds(filepath: str) -> List[str]:
    try:
        with open(filepath, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []

def group_by_standard(targets: Set[Address]) -> Dict[str, Set[Address]]:
    groups = {'BIP44': set(), 'BIP49': set(), 'BIP84': set(), 'BIP86': set()}
    for addr in targets:
        std = get_standard_from_address(addr.value)
        groups[std].add(addr)
    return groups

class InMemoryTargetRepository:
    def __init__(self, targets: Set[Address]):
        self._targets = set(targets)
        self._found = set()

    def get_remaining(self) -> Set[Address]:
        return self._targets - self._found

    def mark_found(self, address: Address) -> None:
        self._found.add(address)

class ConsoleResultSaver:
    def save(self, result):
        import json
        import time
        from pathlib import Path
        out_dir = Path('found')
        out_dir.mkdir(exist_ok=True)
        filename = out_dir / f"found_{result.address.value}_{int(time.time())}.json"
        with open(filename, 'w') as f:
            json.dump({
                'mnemonic': result.mnemonic.phrase,
                'passphrase': result.mnemonic.passphrase,
                'address': result.address.value,
                'standard': result.standard,
                'path': result.derivation_path,
                'platform': result.platform,
                'seed_hex': result.seed_hex
            }, f, indent=2)
        from infrastructure.logger import get_logger
        get_logger().info(f"Result saved to {filename}")