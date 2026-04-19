import json
import os

class Checkpoint:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.data = {}
        self.load()

    def load(self) -> None:
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r') as f:
                self.data = json.load(f)

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, 'w') as f:
            json.dump(self.data, f, indent=2)