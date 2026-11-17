from dataclasses import dataclass

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Exchange, LearningSession, User
from app.models.enums import ExchangeStatus, SessionStatus, SkillKind
from app.services.rewards import BADGE_INFO, Badge
from app.services.rules import POINTS_PER_LEVEL


def level_for(points: int) -> int:
    return points // POINTS_PER_LEVEL + 1


@dataclass(frozen=True)
class Progress:
    points: int
    level: int
    points_to_next_level: int
    verified_skills: int
    completed_exchanges: int
    completed_sessions: int
    learning_goals: list[str]
    achievements: list[tuple[Badge, object]]


def build_progress(db: Session, user: User) -> Progress:
    db.refresh(user)
    participates = or_(Exchange.requester_id == user.id, Exchange.partner_id == user.id)
    completed_exchanges = db.scalar(
        select(func.count(Exchange.id)).where(participates, Exchange.status == ExchangeStatus.COMPLETED)
    )
    completed_sessions = db.scalar(
        select(func.count(LearningSession.id))
        .join(Exchange, Exchange.id == LearningSession.exchange_id)
        .where(participates, LearningSession.status == SessionStatus.COMPLETED)
    )
    level = level_for(user.points)
    achievements = [(Badge(a.code), a.awarded_at) for a in user.achievements if a.code in BADGE_INFO]
    return Progress(
        points=user.points,
        level=level,
        points_to_next_level=level * POINTS_PER_LEVEL - user.points,
        verified_skills=sum(1 for link in user.skills if link.kind == SkillKind.TEACH and link.verified),
        completed_exchanges=completed_exchanges,
        completed_sessions=completed_sessions,
        learning_goals=[link.skill.name for link in user.skills if link.kind == SkillKind.LEARN],
        achievements=achievements,
    )
