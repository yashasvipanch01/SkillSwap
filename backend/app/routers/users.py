from fastapi import APIRouter

from app.deps import CurrentUser, DbSession, Limit, Offset
from app.schemas.assessment import AttemptOut
from app.schemas.exchange import ReviewOut
from app.schemas.user import MeOut, PersonOut, ProfileUpdate, ProgressOut, SkillsIn
from app.services import assessments, progress, reviews, users

router = APIRouter(prefix="/users", tags=["users"])


def _me(db, user) -> MeOut:
    rating, count = users.rating_stats(db, [user.id]).get(user.id, (None, 0))
    return MeOut.build(user, rating, count)


@router.get("/me", response_model=MeOut)
def read_me(user: CurrentUser, db: DbSession):
    return _me(db, user)


@router.patch("/me", response_model=MeOut)
def update_me(payload: ProfileUpdate, user: CurrentUser, db: DbSession):
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    return _me(db, users.update_profile(db, user, changes))


@router.put("/me/skills", response_model=MeOut)
def replace_my_skills(payload: SkillsIn, user: CurrentUser, db: DbSession):
    return _me(db, users.set_skills(db, user, payload.teach, payload.learn))


@router.get("/me/progress", response_model=ProgressOut)
def read_my_progress(user: CurrentUser, db: DbSession):
    return ProgressOut.build(progress.build_progress(db, user))


@router.get("/me/attempts", response_model=list[AttemptOut])
def read_my_attempts(user: CurrentUser, db: DbSession, limit: Limit = 20, offset: Offset = 0):
    links = {link.skill_id: link.verified for link in user.skills}
    return [
        AttemptOut.build(
            attempt,
            attempt.assessment.skill.name,
            links.get(attempt.assessment.skill_id, False),
            False,
        )
        for attempt in assessments.attempts_for(db, user, limit, offset)
    ]


@router.get("/{user_id}", response_model=PersonOut)
def read_user(user_id: int, _: CurrentUser, db: DbSession):
    target = users.get_user(db, user_id)
    rating, count = users.rating_stats(db, [user_id]).get(user_id, (None, 0))
    return PersonOut.build(target, rating, count)


@router.get("/{user_id}/reviews", response_model=list[ReviewOut])
def read_user_reviews(
    user_id: int, _: CurrentUser, db: DbSession, limit: Limit = 20, offset: Offset = 0
):
    return [ReviewOut.build(r) for r in reviews.reviews_received(db, user_id, limit, offset)]
