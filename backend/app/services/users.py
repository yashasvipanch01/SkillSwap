import re

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.errors import Conflict, NotFound, RuleViolation, Unauthorized
from app.core.security import hash_password, verify_password
from app.models import Review, User, UserSkill
from app.models.enums import SkillKind
from app.services.rules import MAX_SKILLS_PER_LIST
from app.services.skills import get_or_create_skills


def clean_list(items: list[str]) -> list[str]:
    seen: dict[str, str] = {}
    for item in items:
        value = " ".join(item.split())
        if value:
            seen.setdefault(value.casefold(), value)
    return list(seen.values())


def _unique_username(db: Session, name: str) -> str:
    base = "@" + (re.sub(r"[^a-z0-9]", "", name.lower())[:20] or "user")
    candidate, suffix = base, 1
    while db.scalar(select(User.id).where(User.username == candidate)):
        suffix += 1
        candidate = f"{base}{suffix}"
    return candidate


def with_skills(stmt):
    return stmt.options(selectinload(User.skills).selectinload(UserSkill.skill))


def get_user(db: Session, user_id: int) -> User:
    user = db.scalar(with_skills(select(User).where(User.id == user_id)))
    if user is None:
        raise NotFound("User not found")
    return user


def register(db: Session, name: str, email: str, password: str) -> User:
    email = email.strip().lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise Conflict("Email is already registered")
    user = User(
        name=name.strip(),
        email=email,
        username=_unique_username(db, name),
        password_hash=hash_password(password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise Conflict("Email is already registered") from None
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email.strip().lower()))
    if user is None or not verify_password(password, user.password_hash):
        raise Unauthorized("Invalid email or password")
    return user


def update_profile(db: Session, user: User, changes: dict) -> User:
    if "username" in changes and changes["username"] != user.username:
        taken = db.scalar(select(User.id).where(User.username == changes["username"]))
        if taken:
            raise Conflict("Username is already taken")
    for field in ("availability", "preferences"):
        if field in changes:
            changes[field] = clean_list(changes[field])
    for field, value in changes.items():
        setattr(user, field, value)
    db.commit()
    return user


def set_skills(db: Session, user: User, teach: list[str], learn: list[str]) -> User:
    teach, learn = clean_list(teach), clean_list(learn)
    if len(teach) > MAX_SKILLS_PER_LIST or len(learn) > MAX_SKILLS_PER_LIST:
        raise RuleViolation(f"At most {MAX_SKILLS_PER_LIST} skills per list")
    teach_skills = get_or_create_skills(db, teach)
    learn_skills = get_or_create_skills(db, learn)
    overlap = teach_skills.keys() & learn_skills.keys()
    if overlap:
        names = ", ".join(sorted(teach_skills[key].name for key in overlap))
        raise RuleViolation(f"A skill cannot be both taught and learned: {names}")

    desired = {(skill.id, SkillKind.TEACH): skill for skill in teach_skills.values()}
    desired |= {(skill.id, SkillKind.LEARN): skill for skill in learn_skills.values()}
    current = {(link.skill_id, link.kind): link for link in user.skills}

    for key, link in current.items():
        if key not in desired:
            user.skills.remove(link)
    for (skill_id, kind), skill in desired.items():
        if (skill_id, kind) not in current:
            user.skills.append(UserSkill(skill=skill, kind=kind))
    user.onboarding_complete = True
    db.commit()
    return user


def rating_stats(db: Session, user_ids: list[int]) -> dict[int, tuple[float, int]]:
    if not user_ids:
        return {}
    rows = db.execute(
        select(Review.reviewee_id, func.avg(Review.rating), func.count(Review.id))
        .where(Review.reviewee_id.in_(user_ids))
        .group_by(Review.reviewee_id)
    )
    return {user_id: (round(float(avg), 1), count) for user_id, avg, count in rows}
