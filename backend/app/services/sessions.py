from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import Conflict, NotFound, RuleViolation
from app.db.base import utcnow
from app.models import Exchange, LearningSession, User
from app.models.enums import ExchangeStatus, SessionStatus
from app.services.exchanges import get_for_participant


def _require_accepted(exchange: Exchange) -> None:
    if exchange.status is not ExchangeStatus.ACCEPTED:
        raise RuleViolation("Sessions can only be managed while the exchange is accepted")


def create_session(
    db: Session, user: User, exchange_id: int, title: str, objective: str, scheduled_at: datetime
) -> LearningSession:
    exchange = get_for_participant(db, user, exchange_id)
    _require_accepted(exchange)
    session = LearningSession(
        exchange_id=exchange.id, title=title, objective=objective, scheduled_at=scheduled_at
    )
    db.add(session)
    db.commit()
    return session


def list_sessions(db: Session, user: User, exchange_id: int) -> list[LearningSession]:
    exchange = get_for_participant(db, user, exchange_id)
    stmt = (
        select(LearningSession)
        .where(LearningSession.exchange_id == exchange.id)
        .order_by(LearningSession.scheduled_at)
    )
    return list(db.scalars(stmt))


def complete_session(db: Session, user: User, session_id: int) -> LearningSession:
    session = db.get(LearningSession, session_id)
    if session is None:
        raise NotFound("Session not found")
    exchange = get_for_participant(db, user, session.exchange_id)
    _require_accepted(exchange)
    if session.status is SessionStatus.COMPLETED:
        raise Conflict("Session is already completed")
    session.status = SessionStatus.COMPLETED
    session.completed_at = utcnow()
    db.commit()
    return session
