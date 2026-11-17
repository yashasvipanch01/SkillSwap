from typing import Annotated

from fastapi import APIRouter, Query

from app.deps import CurrentUser, DbSession, Limit, Offset
from app.schemas.match import CircleOut, MatchOut
from app.services import matching

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("", response_model=list[MatchOut])
def list_matches(
    user: CurrentUser,
    db: DbSession,
    q: Annotated[str, Query(max_length=60)] = "",
    min_score: Annotated[int, Query(ge=0, le=100)] = 1,
    limit: Limit = 20,
    offset: Offset = 0,
):
    ranked = matching.rank_matches(db, user, q.strip(), min_score, limit, offset)
    return [MatchOut.build(u, m, rating, count) for u, m, rating, count in ranked]


@router.get("/circles", response_model=list[CircleOut])
def list_circles(user: CurrentUser, db: DbSession, limit: Annotated[int, Query(ge=1, le=20)] = 5):
    circles, people = matching.circles_for(db, user, limit)
    return [CircleOut.build(legs, people) for legs in circles]
