from dataclasses import dataclass

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
    significance: float

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
        self.significance = self.earnPerHour / self.price if self.price > 0 else 0
    
    def can_upgrade(self) -> bool:
        return self.is_available \
            and not self.is_expired \
            and self.cooldown_seconds == 0 \
            and self.max_level >= self.level \
            and (self.condition is None or self.condition.get("_type") != "SubscribeTelegramChannel")
