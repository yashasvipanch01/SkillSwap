from enum import StrEnum


class SkillKind(StrEnum):
    TEACH = "teach"
    LEARN = "learn"


class ExchangeStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class SessionStatus(StrEnum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
