import hashlib
import hmac
from typing import List, Tuple
import base58
import coincurve
from domain.entities import Mnemonic, Address
from domain.interfaces import AddressDerivator

class CoinCurveDerivator(AddressDerivator):
    def __init__(self, standard: str, check_change: bool = True, max_index_cache: int = 1000):
        self.standard = standard
        self.check_change = check_change
        self._cached_phrase = None
        self._cached_master_key = None
        self._cached_chain_code = None
        self._cached_seed_hex = None
        self._paths = {}
        for change in (0, 1):
            for idx in range(max_index_cache):
                self._paths[(change, idx)] = f"m/{standard[3:]}/0'/0'/{change}/{idx}"

    @staticmethod
    def _derive_child(private_key: bytes, chain_code: bytes, index: int) -> Tuple[bytes, bytes]:
        if index >= 0x80000000:
            data = b'\x00' + private_key + index.to_bytes(4, 'big')
        else:
            pub = coincurve.PrivateKey(private_key).public_key.format(compressed=True)
            data = pub + index.to_bytes(4, 'big')
        I = hmac.new(chain_code, data, hashlib.sha512).digest()
        Il, Ir = I[:32], I[32:]
        new_priv = (int.from_bytes(Il, 'big') + int.from_bytes(private_key, 'big')) % coincurve.ORDER
        return new_priv.to_bytes(32, 'big'), Ir

    @staticmethod
    def _derive_path(master_priv: bytes, master_chain: bytes, path: List[int]) -> Tuple[bytes, bytes]:
        priv, chain = master_priv, master_chain
        for idx in path:
            priv, chain = CoinCurveDerivator._derive_child(priv, chain, idx)
        return priv, chain

    def derive(self, mnemonic: Mnemonic, limit: int) -> Tuple[List[Tuple[str, str, Address]], str]:
        phrase = mnemonic.phrase
        if phrase != self._cached_phrase:
            seed = hashlib.pbkdf2_hmac(
                'sha512',
                phrase.encode('utf-8'),
                f"mnemonic{mnemonic.passphrase}".encode('utf-8'),
                2048, 64
            )
            self._cached_seed_hex = seed.hex()
            I = hmac.new(b"Bitcoin seed", seed, hashlib.sha512).digest()
            self._cached_master_key = coincurve.PrivateKey(I[:32])
            self._cached_chain_code = I[32:]
            self._cached_phrase = phrase

        master_priv = self._cached_master_key.secret
        master_chain = self._cached_chain_code
        addresses = []
        changes = [0]
        if self.check_change:
            changes.append(1)

        purpose_map = {'BIP44': 44, 'BIP49': 49, 'BIP84': 84, 'BIP86': 86}
        purpose = purpose_map[self.standard]

        for change in changes:
            for idx in range(limit):
                path_indices = [
                    purpose + 0x80000000,
                    0x80000000,
                    0x80000000,
                    change,
                    idx
                ]
                priv, _ = self._derive_path(master_priv, master_chain, path_indices)
                pub = coincurve.PrivateKey(priv).public_key

                if self.standard == 'BIP44':
                    sha = hashlib.sha256(pub.format(compressed=True)).digest()
                    ripe = hashlib.new('ripemd160', sha).digest()
                    addr_bytes = b'\x00' + ripe
                    checksum = hashlib.sha256(hashlib.sha256(addr_bytes).digest()).digest()[:4]
                    addr = base58.b58encode(addr_bytes + checksum).decode()
                elif self.standard == 'BIP49':
                    sha = hashlib.sha256(pub.format(compressed=True)).digest()
                    ripe = hashlib.new('ripemd160', sha).digest()
                    script = b'\x00\x14' + ripe
                    sha_script = hashlib.sha256(script).digest()
                    ripe_script = hashlib.new('ripemd160', sha_script).digest()
                    addr_bytes = b'\x05' + ripe_script
                    checksum = hashlib.sha256(hashlib.sha256(addr_bytes).digest()).digest()[:4]
                    addr = base58.b58encode(addr_bytes + checksum).decode()
                elif self.standard == 'BIP84':
                    addr = coincurve.encoding.bech32_encode('bc', 0, pub.format(compressed=True)[1:])
                elif self.standard == 'BIP86':
                    pub_bytes = pub.format(compressed=True)[1:]
                    addr = coincurve.encoding.bech32_encode('bc', 1, pub_bytes)
                else:
                    raise ValueError(f"Unsupported standard: {self.standard}")

                path_str = self._paths.get((change, idx), f"m/{purpose}/0'/0'/{change}/{idx}")
                addresses.append((self.standard, path_str, Address(addr)))

        return addresses, self._cached_seed_hex