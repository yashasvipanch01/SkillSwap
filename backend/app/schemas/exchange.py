from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator

from app.db.base import utcnow
from app.models import Exchange, LearningSession, Review
from app.models.enums import ExchangeStatus, SessionStatus
from app.schemas.user import PersonBrief
from app.services.exchanges import Role, role_of


class ExchangeIn(BaseModel):
    partner_id: int
    topic: str = Field(min_length=1, max_length=60)
    note: str = Field(default="", max_length=1000)


class ExchangeOut(BaseModel):
    id: int
    status: ExchangeStatus
    topic: str
    note: str
    role: Role
    person: PersonBrief
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None

    @classmethod
    def build(cls, exchange: Exchange, viewer_id: int) -> "ExchangeOut":
        role = role_of(exchange, viewer_id)
        other = exchange.partner if role is Role.REQUESTER else exchange.requester
        return cls(
            id=exchange.id,
            status=exchange.status,
            topic=exchange.skill.name,
            note=exchange.note,
            role=role,
            person=PersonBrief.build(other),
            created_at=exchange.created_at,
            updated_at=exchange.updated_at,
            completed_at=exchange.completed_at,
        )


class SessionIn(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    objective: str = Field(default="", max_length=1000)
    scheduled_at: datetime

    @field_validator("scheduled_at")
    @classmethod
    def must_be_future(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        if value <= utcnow():
            raise ValueError("scheduled_at must be in the future")
        return value


class SessionOut(BaseModel):
    id: int
    exchange_id: int
    title: str
    objective: str
    scheduled_at: datetime
    status: SessionStatus
    completed_at: datetime | None

    @classmethod
    def build(cls, session: LearningSession) -> "SessionOut":
        return cls(
            id=session.id,
            exchange_id=session.exchange_id,
            title=session.title,
            objective=session.objective,
            scheduled_at=session.scheduled_at,
            status=session.status,
            completed_at=session.completed_at,
        )


class ReviewIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str = Field(default="", max_length=1000)


class ReviewOut(BaseModel):
    id: int
    exchange_id: int
    rating: int
    comment: str
    reviewer: PersonBrief
    created_at: datetime

    @classmethod
    def build(cls, review: Review) -> "ReviewOut":
        return cls(
            id=review.id,
            exchange_id=review.exchange_id,
            rating=review.rating,
            comment=review.comment,
            reviewer=PersonBrief.build(review.reviewer),
            created_at=review.created_at,
        )
