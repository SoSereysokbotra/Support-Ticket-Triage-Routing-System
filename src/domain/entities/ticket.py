import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from src.domain.entities.category import TicketCategory, TicketUrgency


@dataclass
class Ticket:
    """
    Pure Domain Entity representing a support ticket.
    Contains business invariants and validation logic.
    """
    body: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: Optional[str] = None
    customer_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    actual_category: Optional[TicketCategory] = None
    actual_urgency: Optional[TicketUrgency] = None

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not self.body or not self.body.strip():
            raise ValueError("Ticket body cannot be empty or whitespace only.")
        if len(self.body.strip()) < 5:
            raise ValueError("Ticket body must be at least 5 characters long.")
        if len(self.body) > 10000:
            raise ValueError("Ticket body exceeds maximum allowed length of 10,000 characters.")

    @property
    def full_text(self) -> str:
        """Combines title and body for NLP classification."""
        if self.title and self.title.strip():
            return f"{self.title.strip()}. {self.body.strip()}"
        return self.body.strip()
