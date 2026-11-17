import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models import User
from app.models.enums import SkillKind
from app.services.progress import Progress
from app.services.rewards import BADGE_INFO

USERNAME_PATTERN = re.compile(r"^@?[a-z0-9_]{3,30}$")


def initials_of(name: str) -> str:
    return "".join(part[0] for part in name.split()[:2]).upper()


class PersonBrief(BaseModel):
    id: int
    name: str
    username: str
    initials: str

    @classmethod
    def build(cls, user: User) -> "PersonBrief":
        return cls(id=user.id, name=user.name, username=user.username, initials=initials_of(user.name))


class PersonOut(PersonBrief):
    bio: str
    teach: list[str]
    learn: list[str]
    verified: list[str]
    preferences: list[str]
    availability: list[str]
    points: int
    rating: float | None
    rating_count: int

    @classmethod
    def build(cls, user: User, rating: float | None = None, rating_count: int = 0) -> "PersonOut":
        teach = [link for link in user.skills if link.kind == SkillKind.TEACH]
        return cls(
            id=user.id,
            name=user.name,
            username=user.username,
            initials=initials_of(user.name),
            bio=user.bio,
            teach=[link.skill.name for link in teach],
            learn=[link.skill.name for link in user.skills if link.kind == SkillKind.LEARN],
            verified=[link.skill.name for link in teach if link.verified],
            preferences=user.preferences,
            availability=user.availability,
            points=user.points,
            rating=rating,
            rating_count=rating_count,
        )


class MeOut(PersonOut):
    email: str
    onboarding_complete: bool

    @classmethod
    def build(cls, user: User, rating: float | None = None, rating_count: int = 0) -> "MeOut":
        base = PersonOut.build(user, rating, rating_count)
        return cls(**base.model_dump(), email=user.email, onboarding_complete=user.onboarding_complete)


class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)

    @field_validator("name")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Name must not be blank")
        return value.strip()


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: MeOut


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=120)
    username: str | None = None
    bio: str | None = Field(default=None, max_length=500)
    availability: list[str] | None = Field(default=None, max_length=20)
    preferences: list[str] | None = Field(default=None, max_length=20)

    @field_validator("username")
    @classmethod
    def valid_username(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip().lower()
        if not USERNAME_PATTERN.match(value):
            raise ValueError("Username must be 3-30 characters: letters, digits or underscore")
        return value if value.startswith("@") else f"@{value}"


class SkillsIn(BaseModel):
    teach: list[str] = Field(default_factory=list, max_length=40)
    learn: list[str] = Field(default_factory=list, max_length=40)

    @field_validator("teach", "learn")
    @classmethod
    def names_not_too_long(cls, values: list[str]) -> list[str]:
        if any(len(v) > 60 for v in values):
            raise ValueError("Skill names must be 60 characters or fewer")
        return values


class AchievementOut(BaseModel):
    code: str
    title: str
    description: str
    awarded_at: datetime


class ProgressOut(BaseModel):
    points: int
    level: int
    points_to_next_level: int
    verified_skills: int
    completed_exchanges: int
    completed_sessions: int
    learning_goals: list[str]
    achievements: list[AchievementOut]

    @classmethod
    def build(cls, progress: Progress) -> "ProgressOut":
        achievements = [
            AchievementOut(
                code=badge.value,
                title=BADGE_INFO[badge][0],
                description=BADGE_INFO[badge][1],
                awarded_at=awarded_at,
            )
            for badge, awarded_at in progress.achievements
        ]
        return cls(
            points=progress.points,
            level=progress.level,
            points_to_next_level=progress.points_to_next_level,
            verified_skills=progress.verified_skills,
            completed_exchanges=progress.completed_exchanges,
            completed_sessions=progress.completed_sessions,
            learning_goals=progress.learning_goals,
            achievements=achievements,
        )


class SkillOut(BaseModel):
    id: int
    name: str
