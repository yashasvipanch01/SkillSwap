from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User
from app.models.enums import SkillKind
from app.services.users import rating_stats, with_skills

TEACHES_ME_WEIGHT = 40
LEARNS_FROM_ME_WEIGHT = 30
AVAILABILITY_WEIGHT = 15
PREFERENCE_WEIGHT = 10
VERIFIED_WEIGHT = 5


@dataclass(frozen=True)
class Profile:
    user_id: int
    teach: dict[int, str]
    learn: dict[int, str]
    verified: frozenset[int]
    availability: dict[str, str]
    preferences: dict[str, str]

    @classmethod
    def from_user(cls, user: User) -> "Profile":
        teach = {link.skill_id: link.skill.name for link in user.skills if link.kind == SkillKind.TEACH}
        learn = {link.skill_id: link.skill.name for link in user.skills if link.kind == SkillKind.LEARN}
        verified = frozenset(
            link.skill_id for link in user.skills if link.kind == SkillKind.TEACH and link.verified
        )
        return cls(
            user_id=user.id,
            teach=teach,
            learn=learn,
            verified=verified,
            availability={x.casefold(): x for x in user.availability},
            preferences={x.casefold(): x for x in user.preferences},
        )


@dataclass(frozen=True)
class Match:
    score: int
    teaches_me: list[str] = field(default_factory=list)
    learns_from_me: list[str] = field(default_factory=list)
    shared_availability: list[str] = field(default_factory=list)
    shared_preferences: list[str] = field(default_factory=list)

    @property
    def reciprocal(self) -> bool:
        return bool(self.teaches_me and self.learns_from_me)


def skills_given(giver: Profile, receiver: Profile) -> list[str]:
    return sorted(giver.teach[sid] for sid in giver.teach.keys() & receiver.learn.keys())


def compatibility(me: Profile, other: Profile) -> Match:
    teaches_me = skills_given(other, me)
    learns_from_me = skills_given(me, other)
    shared_availability = sorted(
        other.availability[key] for key in other.availability.keys() & me.availability.keys()
    )
    shared_preferences = sorted(
        other.preferences[key] for key in other.preferences.keys() & me.preferences.keys()
    )
    score = 0
    if teaches_me:
        score += TEACHES_ME_WEIGHT
        if other.verified & (other.teach.keys() & me.learn.keys()):
            score += VERIFIED_WEIGHT
    if learns_from_me:
        score += LEARNS_FROM_ME_WEIGHT
    if shared_availability:
        score += AVAILABILITY_WEIGHT
    if shared_preferences:
        score += PREFERENCE_WEIGHT
    return Match(score, teaches_me, learns_from_me, shared_availability, shared_preferences)


@dataclass(frozen=True)
class Leg:
    giver_id: int
    receiver_id: int
    skills: list[str]


def find_circles(me: Profile, others: list[Profile], limit: int = 10) -> list[list[Leg]]:
    circles: list[list[Leg]] = []
    for second in others:
        first_leg = skills_given(me, second)
        if not first_leg or skills_given(second, me):
            continue
        for third in others:
            if third.user_id == second.user_id:
                continue
            second_leg = skills_given(second, third)
            third_leg = skills_given(third, me)
            if second_leg and third_leg:
                circles.append(
                    [
                        Leg(me.user_id, second.user_id, first_leg),
                        Leg(second.user_id, third.user_id, second_leg),
                        Leg(third.user_id, me.user_id, third_leg),
                    ]
                )
                if len(circles) >= limit:
                    return circles
    return circles


def _matches_query(user: User, query: str) -> bool:
    haystack = " ".join([user.name, *(link.skill.name for link in user.skills)]).casefold()
    return query.casefold() in haystack


def rank_matches(
    db: Session, me: User, query: str, min_score: int, limit: int, offset: int
) -> list[tuple[User, Match, float | None, int]]:
    others = list(db.scalars(with_skills(select(User).where(User.id != me.id))))
    my_profile = Profile.from_user(me)
    scored = []
    for user in others:
        if query and not _matches_query(user, query):
            continue
        match = compatibility(my_profile, Profile.from_user(user))
        if match.score >= min_score:
            scored.append((user, match))

    stats = rating_stats(db, [user.id for user, _ in scored])
    scored.sort(key=lambda item: (-item[1].score, -stats.get(item[0].id, (0.0, 0))[0], item[0].name))
    page = scored[offset : offset + limit]
    return [(user, match, *stats.get(user.id, (None, 0))) for user, match in page]


def circles_for(db: Session, me: User, limit: int) -> tuple[list[list[Leg]], dict[int, User]]:
    others = list(db.scalars(with_skills(select(User).where(User.id != me.id))))
    circles = find_circles(
        Profile.from_user(me), [Profile.from_user(user) for user in others], limit
    )
    people = {user.id: user for user in others} | {me.id: me}
    return circles, people
