from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Skill


def normalize(name: str) -> str:
    return " ".join(name.split())


def key_of(name: str) -> str:
    return normalize(name).casefold()


def get_or_create_skills(db: Session, names: Iterable[str]) -> dict[str, Skill]:
    wanted = {key_of(name): normalize(name) for name in names if normalize(name)}
    if not wanted:
        return {}
    found = {
        skill.name_key: skill
        for skill in db.scalars(select(Skill).where(Skill.name_key.in_(list(wanted))))
    }
    for key, name in wanted.items():
        if key not in found:
            skill = Skill(name=name, name_key=key)
            db.add(skill)
            found[key] = skill
    db.flush()
    return found


def find_skill(db: Session, name: str) -> Skill | None:
    return db.scalar(select(Skill).where(Skill.name_key == key_of(name)))


def search_skills(db: Session, query: str, limit: int) -> list[Skill]:
    stmt = select(Skill).order_by(Skill.name).limit(limit)
    if query.strip():
        stmt = stmt.where(Skill.name_key.contains(key_of(query)))
    return list(db.scalars(stmt))
