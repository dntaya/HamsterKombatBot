from dataclasses import dataclass
from time import time


@dataclass
class Profile:
    balance: float
    earn_per_hour: float
    earn_per_sec: float
    available_energy: int
    energy_recover_per_sec: int
    earn_per_tap: float
    max_energy: int
    update_time: int
    last_passive_earn: float
    exchange_id: str | None
    last_energy_boost_time: int

    def __init__(self, data: dict):
        self.balance = data.get('balanceCoins', 0)
        self.earn_per_hour = data.get('earnPassivePerHour', 0)
        self.earn_per_sec = data.get('earnPassivePerSec', 0)
        self.available_energy = data.get('availableTaps', 0)
        self.energy_recover_per_sec = data.get('tapsRecoverPerSec', 0)
        self.earn_per_tap = data.get('earnPerTap', 0)
        self.max_energy = data.get('maxTaps', 0)
        self.last_passive_earn = data.get('lastPassiveEarn', 0)
        self.exchange_id = data.get('exchangeId')
        self.update_time = time()
        try: 
            self.last_energy_boost_time = next((boost for boost in data["boosts"] if boost['id'] == 'BoostFullAvailableTaps'), {}).get("lastUpgradeAt", 0)
        except:
            self.last_energy_boost_time = 0

    def getAvailableTaps(self):
        return int(float(self.available_energy) / self.earn_per_tap)
    
@dataclass
class Upgrade:
    id: str
    name: str
    level: int
    price: float
    earn_per_hour: float
    is_available: bool
    is_expired: bool
    cooldown_seconds: int
    max_level: int
    condition: str

    def __init__(self, data: dict):
        self.id = data["id"]
        self.name = data["name"]
        self.level = data["level"]
        self.price = data["price"]
        self.earn_per_hour = data["profitPerHourDelta"]
        self.is_available = data["isAvailable"]
        self.is_expired = data["isExpired"]
        self.cooldown_seconds = data.get("cooldownSeconds", 0)
        self.max_level = data.get("maxLevel", data["level"])
        self.condition = data.get("condition")

    def calculate_significance(self) -> float:
        return self.price / self.earn_per_hour + self.cooldown_seconds / 3600
    
    def can_upgrade(self) -> bool:
        return self.is_available \
            and not self.is_expired \
            and self.earn_per_hour != 0 \
            and self.max_level >= self.level \
            and (self.condition is None or self.condition.get("_type") != "SubscribeTelegramChannel")


@dataclass
class ProfileAndUpgrades:
    profile: Profile
    upgrades: list[Upgrade]

@dataclass
class Boost:
    id: str
    cooldown_seconds: int
    level: int
    max_level: int

    def __init__(self, data: dict):
        self.id = data["id"]
        self.cooldown_seconds = data.get("cooldownSeconds", 0)
        self.level = data.get("level", 0)
        self.max_level = data.get("maxLevel", self.level)

@dataclass
class Task:
    id: str
    is_completed: bool
    rewards_by_days: list[int]
    days: int

    def __init__(self, data: dict):
        self.id = data["id"]
        self.is_completed = data["isCompleted"]
        self.rewards_by_days = list(map(lambda d: d.get("rewardCoins", 0), data.get("rewardsByDays", [])))
        self.days = data.get("days", 0)

@dataclass
class DailyCipher:
    cipher: str
    bonus_coins: int
    is_claimed: bool

    def __init__(self, data: dict):
        self.cipher = data["cipher"]
        self.bonus_coins = data["bonusCoins"]
        self.is_claimed = data["isClaimed"]

@dataclass
class Config:
    daily_cipher: DailyCipher

    def __init__(self, data: dict):
        self.daily_cipher = DailyCipher(data=data["dailyCipher"])
