from enum import Enum


class TicketCategory(str, Enum):
    HARDWARE = "Hardware"
    SOFTWARE = "Software"
    NETWORK = "Network"
    ACCESS_SECURITY = "Access & Security"
    BILLING_ADMIN = "Billing & Admin"
    OTHER = "Other"

    @classmethod
    def list_categories(cls) -> list[str]:
        return [c.value for c in cls]

    @classmethod
    def from_str(cls, value: str) -> "TicketCategory":
        normalized = value.strip().lower()
        for cat in cls:
            if cat.value.lower() == normalized or cat.name.lower() == normalized:
                return cat
        return cls.OTHER


class TicketUrgency(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

    @classmethod
    def from_str(cls, value: str) -> "TicketUrgency":
        normalized = value.strip().lower()
        for urg in cls:
            if urg.value.lower() == normalized or urg.name.lower() == normalized:
                return urg
        return cls.MEDIUM
