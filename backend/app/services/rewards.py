from enum import StrEnum

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Achievement, Review, User


class Badge(StrEnum):
    VERIFIED_TEACHER = "verified_teacher"
    FIRST_EXCHANGE = "first_exchange"
    HIGHLY_RATED = "highly_rated"


BADGE_INFO = {
    Badge.VERIFIED_TEACHER: ("Verified teacher", "Passed a skill assessment with 75% or higher."),
    Badge.FIRST_EXCHANGE: ("First exchange", "Completed a first skill exchange."),
    Badge.HIGHLY_RATED: ("Highly rated", "Average rating of 4.5 or more across 3 or more reviews."),
}

HIGHLY_RATED_MIN_REVIEWS = 3
HIGHLY_RATED_MIN_AVERAGE = 4.5


def award_points(user: User, amount: int) -> None:
    user.points = User.points + amount


def grant_badge(db: Session, user: User, badge: Badge) -> bool:
    already = db.scalar(
        select(Achievement.id).where(Achievement.user_id == user.id, Achievement.code == badge.value)
    )
    if already:
        return False
    db.add(Achievement(user_id=user.id, code=badge.value))
    return True


def grant_highly_rated_if_eligible(db: Session, user_id: int) -> None:
    count, average = db.execute(
        select(func.count(Review.id), func.avg(Review.rating)).where(Review.reviewee_id == user_id)
    ).one()
    if count >= HIGHLY_RATED_MIN_REVIEWS and average >= HIGHLY_RATED_MIN_AVERAGE:
        user = db.get(User, user_id)
        grant_badge(db, user, Badge.HIGHLY_RATED)
