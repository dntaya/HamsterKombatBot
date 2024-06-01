from dataclasses import dataclass
from time import time

@dataclass
class Profile:
    balance: float
    earn_per_hour: float
    available_energy: int
    energy_recover_per_sec: int
    earn_per_tap: float
    max_energy: int
    update_time: float

    def __init__(self, data: dict):
        self.balance = data.get('balanceCoins', 0)
        self.earn_per_hour = data.get('earnPassivePerHour', 0)
        self.available_energy = data.get('availableTaps', 0)
        self.energy_recover_per_sec = data.get('tapsRecoverPerSec', 0)
        self.earn_per_tap = data.get('earnPerTap', 0)
        self.max_energy = data.get('maxTaps', 0)
        self.update_time = time()

    def getAvailableTaps(self):
        return int(float(self.available_energy) / self.earn_per_tap)