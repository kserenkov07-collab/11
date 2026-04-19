import random
import secrets
from typing import Iterator
from bip_utils import Bip39MnemonicGenerator
from domain.entities import Mnemonic
from domain.interfaces import MnemonicGenerator
from .checkpoint import Checkpoint

class UniqueWordsGenerator(MnemonicGenerator):
    """Генератор с опциональной проверкой уникальности слов."""

    def __init__(self, mode: str = 'counter', seed: int = None,
                 checkpoint: Checkpoint = None, require_unique: bool = False):
        self.mode = mode
        self.require_unique = require_unique
        self.checkpoint = checkpoint or Checkpoint('data/checkpoint.json')
        self.counter = 0
        self.rng = None

        if self.mode == 'counter':
            seed = seed or self.checkpoint.data.get('seed')
            if seed is None:
                seed = secrets.randbits(256)
                self.checkpoint.data['seed'] = seed
            self.rng = random.Random(seed)

            if 'rng_state' in self.checkpoint.data:
                self.rng.setstate(self._decode_state(self.checkpoint.data['rng_state']))
            self.counter = self.checkpoint.data.get('counter', 0)

    def _encode_state(self, state):
        return (state[0], state[1], state[2])

    def _decode_state(self, enc_state):
        return (enc_state[0], tuple(enc_state[1]), enc_state[2])

    def _generate_raw(self) -> str:
        if self.mode == 'counter':
            entropy = self.rng.getrandbits(128).to_bytes(16, 'big')
        else:
            entropy = secrets.token_bytes(16)
        mnemonic_obj = Bip39MnemonicGenerator().FromEntropy(entropy)
        return str(mnemonic_obj)

    def _is_valid(self, phrase: str) -> bool:
        if not self.require_unique:
            return True
        words = phrase.split()
        return len(words) == len(set(words))

    def generate(self) -> Iterator[Mnemonic]:
        while True:
            phrase = self._generate_raw()
            while not self._is_valid(phrase):
                phrase = self._generate_raw()
            self.counter += 1
            self.checkpoint.data['counter'] = self.counter
            yield Mnemonic(phrase=phrase)

    def save_state(self) -> None:
        if self.mode == 'counter':
            self.checkpoint.data['rng_state'] = self._encode_state(self.rng.getstate())
            self.checkpoint.save()
