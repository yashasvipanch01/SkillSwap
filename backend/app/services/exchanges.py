from dataclasses import dataclass
from enum import StrEnum

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import Conflict, Forbidden, NotFound, RuleViolation
from app.db.base import utcnow
from app.models import Exchange, User, UserSkill
from app.models.enums import ExchangeStatus, SkillKind
from app.services import rewards
from app.services.rules import POINTS_COMPLETE_EXCHANGE
from app.services.skills import find_skill

OPEN_STATUSES = (ExchangeStatus.PENDING, ExchangeStatus.ACCEPTED)


class Role(StrEnum):
    REQUESTER = "requester"
    PARTNER = "partner"


class Action(StrEnum):
    ACCEPT = "accept"
    REJECT = "reject"
    CANCEL = "cancel"
    COMPLETE = "complete"


@dataclass(frozen=True)
class Transition:
    sources: frozenset[ExchangeStatus]
    target: ExchangeStatus
    roles: frozenset[Role]


BOTH = frozenset(Role)

TRANSITIONS = {
    Action.ACCEPT: Transition(
        frozenset({ExchangeStatus.PENDING}), ExchangeStatus.ACCEPTED, frozenset({Role.PARTNER})
    ),
    Action.REJECT: Transition(
        frozenset({ExchangeStatus.PENDING}), ExchangeStatus.REJECTED, frozenset({Role.PARTNER})
    ),
    Action.CANCEL: Transition(frozenset(OPEN_STATUSES), ExchangeStatus.CANCELLED, BOTH),
    Action.COMPLETE: Transition(
        frozenset({ExchangeStatus.ACCEPTED}), ExchangeStatus.COMPLETED, BOTH
    ),
}


def role_of(exchange: Exchange, user_id: int) -> Role | None:
    if exchange.requester_id == user_id:
        return Role.REQUESTER
    if exchange.partner_id == user_id:
        return Role.PARTNER
    return None


def _loaded():
    return (
        selectinload(Exchange.requester),
        selectinload(Exchange.partner),
        selectinload(Exchange.skill),
    )


def get_for_participant(
    db: Session, user: User, exchange_id: int, lock: bool = False
) -> Exchange:
    stmt = select(Exchange).where(Exchange.id == exchange_id).options(*_loaded())
    if lock:
        stmt = stmt.with_for_update()
    exchange = db.scalar(stmt)
    if exchange is None or role_of(exchange, user.id) is None:
        raise NotFound("Exchange not found")
    return exchange


def create_exchange(db: Session, user: User, partner_id: int, topic: str, note: str) -> Exchange:
    if partner_id == user.id:
        raise RuleViolation("You cannot start an exchange with yourself")
    partner = db.get(User, partner_id)
    if partner is None:
        raise NotFound("Partner not found")
    skill = find_skill(db, topic)
    teaches = skill and db.scalar(
        select(UserSkill.id).where(
            UserSkill.user_id == partner.id,
            UserSkill.skill_id == skill.id,
            UserSkill.kind == SkillKind.TEACH,
        )
    )
    if not teaches:
        raise RuleViolation(f"{partner.name} does not teach {topic.strip()}")

    duplicate = db.scalar(
        select(Exchange.id).where(
            Exchange.requester_id == user.id,
            Exchange.partner_id == partner.id,
            Exchange.skill_id == skill.id,
            Exchange.status.in_(OPEN_STATUSES),
        )
    )
    if duplicate:
        raise Conflict("You already have an open exchange with this person for this skill")

    exchange = Exchange(requester_id=user.id, partner_id=partner.id, skill_id=skill.id, note=note)
    db.add(exchange)
    db.commit()
    return get_for_participant(db, user, exchange.id)


def list_exchanges(
    db: Session, user: User, status: ExchangeStatus | None, limit: int, offset: int
) -> list[Exchange]:
    stmt = (
        select(Exchange)
        .where(or_(Exchange.requester_id == user.id, Exchange.partner_id == user.id))
        .options(*_loaded())
        .order_by(Exchange.created_at.desc(), Exchange.id.desc())
        .limit(limit)
        .offset(offset)
    )
    if status:
        stmt = stmt.where(Exchange.status == status)
    return list(db.scalars(stmt))


def apply_action(db: Session, user: User, exchange_id: int, action: Action) -> Exchange:
    exchange = get_for_participant(db, user, exchange_id, lock=True)
    transition = TRANSITIONS[action]
    role = role_of(exchange, user.id)
    if role not in transition.roles:
        allowed = " or ".join(sorted(r.value for r in transition.roles))
        raise Forbidden(f"Only the {allowed} can {action.value} this exchange")
    if exchange.status not in transition.sources:
        raise Conflict(f"Cannot {action.value} an exchange that is {exchange.status.value}")

    exchange.status = transition.target
    if action is Action.COMPLETE:
        exchange.completed_at = utcnow()
        for participant in (exchange.requester, exchange.partner):
            rewards.award_points(participant, POINTS_COMPLETE_EXCHANGE)
            rewards.grant_badge(db, participant, rewards.Badge.FIRST_EXCHANGE)
    db.commit()
    return exchange
