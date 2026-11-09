import sys
from pathlib import Path

import pytest

# Les modules importent `config` à la racine de l'application
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class FakeClock:
    """Horloge contrôlable pour tester la logique temporelle."""

    def __init__(self, start=1000.0):
        self.now = start

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


@pytest.fixture
def clock():
    return FakeClock()
