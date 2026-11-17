from typing import Annotated

from fastapi import APIRouter, Query

from app.deps import CurrentUser, DbSession, Limit
from app.schemas.user import SkillOut
from app.services import skills

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("", response_model=list[SkillOut])
def search_skills(
    _: CurrentUser, db: DbSession, q: Annotated[str, Query(max_length=60)] = "", limit: Limit = 20
):
    return [SkillOut(id=s.id, name=s.name) for s in skills.search_skills(db, q, limit)]
