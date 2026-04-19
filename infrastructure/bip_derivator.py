from typing import List, Tuple
from bip_utils import (
    Bip39SeedGenerator, Bip44, Bip49, Bip84, Bip86,
    Bip44Coins, Bip49Coins, Bip84Coins, Bip86Coins, Bip44Changes
)
from domain.entities import Mnemonic, Address
from domain.interfaces import AddressDerivator

class SingleStandardDerivator(AddressDerivator):
    """Деривация адресов только для одного стандарта с кэшированием мастер-ключа и путей."""

    def __init__(self, standard: str, check_change: bool = True, max_index_cache: int = 1000):
        self.standard = standard
        self.check_change = check_change
        self._cached_phrase = None
        self._cached_master = None
        self._cached_seed_hex = None
        # Предвычисление путей деривации
        self._paths = {}
        for change in (0, 1):
            for idx in range(max_index_cache):
                self._paths[(change, idx)] = f"m/{standard[3:]}/0'/0'/{change}/{idx}"

    def derive(self, mnemonic: Mnemonic, limit: int) -> Tuple[List[Tuple[str, str, Address]], str]:
        phrase = mnemonic.phrase
        if phrase != self._cached_phrase:
            seed = Bip39SeedGenerator(phrase).Generate(mnemonic.passphrase)
            self._cached_seed_hex = seed.hex()

            if self.standard == 'BIP44':
                self._cached_master = Bip44.FromSeed(seed, Bip44Coins.BITCOIN)
            elif self.standard == 'BIP49':
                self._cached_master = Bip49.FromSeed(seed, Bip49Coins.BITCOIN)
            elif self.standard == 'BIP84':
                self._cached_master = Bip84.FromSeed(seed, Bip84Coins.BITCOIN)
            elif self.standard == 'BIP86':
                self._cached_master = Bip86.FromSeed(seed, Bip86Coins.BITCOIN)
            else:
                raise ValueError(f"Unsupported standard: {self.standard}")

            self._cached_phrase = phrase

        addresses = []
        changes = [Bip44Changes.CHAIN_EXT]
        if self.check_change:
            changes.append(Bip44Changes.CHAIN_INT)

        for change in changes:
            for idx in range(limit):
                addr = (self._cached_master.Purpose().Coin().Account(0)
                        .Change(change).AddressIndex(idx).PublicKey().ToAddress())
                path = self._paths.get((change, idx), f"m/{self.standard[3:]}/0'/0'/{change}/{idx}")
                addresses.append((self.standard, path, Address(addr)))

        return addresses, self._cached_seed_hex