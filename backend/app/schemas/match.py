from pydantic import BaseModel

from app.models import User
from app.schemas.user import PersonBrief, PersonOut
from app.services.matching import Leg, Match


class MatchOut(BaseModel):
    person: PersonOut
    score: int
    reciprocal: bool
    they_teach_you: list[str]
    you_teach_them: list[str]
    shared_availability: list[str]
    shared_preferences: list[str]

    @classmethod
    def build(cls, user: User, match: Match, rating: float | None, count: int) -> "MatchOut":
        return cls(
            person=PersonOut.build(user, rating, count),
            score=match.score,
            reciprocal=match.reciprocal,
            they_teach_you=match.teaches_me,
            you_teach_them=match.learns_from_me,
            shared_availability=match.shared_availability,
            shared_preferences=match.shared_preferences,
        )


class LegOut(BaseModel):
    giver: PersonBrief
    receiver: PersonBrief
    skills: list[str]


class CircleOut(BaseModel):
    legs: list[LegOut]

    @classmethod
    def build(cls, legs: list[Leg], people: dict[int, User]) -> "CircleOut":
        return cls(
            legs=[
                LegOut(
                    giver=PersonBrief.build(people[leg.giver_id]),
                    receiver=PersonBrief.build(people[leg.receiver_id]),
                    skills=leg.skills,
                )
                for leg in legs
            ]
        )
