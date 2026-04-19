from abc import ABC, abstractmethod
from typing import Iterator, List, Set, Tuple
from .entities import Mnemonic, Address, ScanResult

class MnemonicGenerator(ABC):
    @abstractmethod
    def generate(self) -> Iterator[Mnemonic]:
        pass

    @abstractmethod
    def save_state(self) -> None:
        pass

class AddressDerivator(ABC):
    @abstractmethod
    def derive(self, mnemonic: Mnemonic, limit: int) -> Tuple[List[Tuple[str, str, Address]], str]:
        """Return list of (standard, path, Address) and seed_hex."""
        pass

class TargetRepository(ABC):
    @abstractmethod
    def get_remaining(self) -> Set[Address]:
        pass

    @abstractmethod
    def mark_found(self, address: Address) -> None:
        pass

class ResultSaver(ABC):
    @abstractmethod
    def save(self, result: ScanResult) -> None:
        pass