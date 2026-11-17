from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.errors import Conflict, RuleViolation
from app.models import Exchange, Review, User
from app.models.enums import ExchangeStatus
from app.services import rewards
from app.services.exchanges import get_for_participant
from app.services.rules import POINTS_WRITE_REVIEW
from app.services.users import get_user


def create_review(
    db: Session, user: User, exchange_id: int, rating: int, comment: str
) -> Review:
    exchange: Exchange = get_for_participant(db, user, exchange_id)
    if exchange.status is not ExchangeStatus.COMPLETED:
        raise RuleViolation("Reviews can only be written after the exchange is completed")
    reviewee_id = exchange.partner_id if exchange.requester_id == user.id else exchange.requester_id

    review = Review(
        exchange_id=exchange.id,
        reviewer_id=user.id,
        reviewee_id=reviewee_id,
        rating=rating,
        comment=comment,
    )
    db.add(review)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise Conflict("You have already reviewed this exchange") from None

    rewards.award_points(user, POINTS_WRITE_REVIEW)
    rewards.grant_highly_rated_if_eligible(db, reviewee_id)
    db.commit()
    return review


def reviews_received(db: Session, user_id: int, limit: int, offset: int) -> list[Review]:
    get_user(db, user_id)
    stmt = (
        select(Review)
        .where(Review.reviewee_id == user_id)
        .options(selectinload(Review.reviewer))
        .order_by(Review.created_at.desc(), Review.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt))
