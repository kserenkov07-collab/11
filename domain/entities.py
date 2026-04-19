from dataclasses import dataclass

@dataclass(frozen=True)
class Address:
    value: str

    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Address must be a non-empty string")

@dataclass(frozen=True)
class Mnemonic:
    phrase: str
    passphrase: str = ""

@dataclass
class ScanResult:
    mnemonic: Mnemonic
    address: Address
    standard: str          # 'BIP44', 'BIP49', 'BIP84', 'BIP86'
    derivation_path: str
    platform: str
    seed_hex: str