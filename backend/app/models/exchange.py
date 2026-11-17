from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, enum_column, utcnow
from app.models.enums import ExchangeStatus, SessionStatus
from app.models.skill import Skill
from app.models.user import User


class Exchange(Base):
    __tablename__ = "exchanges"
    __table_args__ = (Index("ix_exchanges_status", "status"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    partner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"))
    note: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[ExchangeStatus] = enum_column(ExchangeStatus, default=ExchangeStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    requester: Mapped[User] = relationship(foreign_keys=[requester_id])
    partner: Mapped[User] = relationship(foreign_keys=[partner_id])
    skill: Mapped[Skill] = relationship()
    sessions: Mapped[list["LearningSession"]] = relationship(
        back_populates="exchange", cascade="all, delete-orphan", order_by="LearningSession.scheduled_at"
    )


class LearningSession(Base):
    __tablename__ = "learning_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    exchange_id: Mapped[int] = mapped_column(
        ForeignKey("exchanges.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(120))
    objective: Mapped[str] = mapped_column(Text, default="")
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[SessionStatus] = enum_column(SessionStatus, default=SessionStatus.SCHEDULED)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    exchange: Mapped[Exchange] = relationship(back_populates="sessions")


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("exchange_id", "reviewer_id"),
        CheckConstraint("rating BETWEEN 1 AND 5", name="ck_reviews_rating_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    exchange_id: Mapped[int] = mapped_column(ForeignKey("exchanges.id", ondelete="CASCADE"))
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    reviewee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    rating: Mapped[int]
    comment: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    reviewer: Mapped[User] = relationship(foreign_keys=[reviewer_id])
