from datetime import datetime

from pydantic import BaseModel, Field

from app.models import Assessment, AssessmentAttempt
from app.services.rules import PASS_MARK


class AssessmentSummary(BaseModel):
    id: int
    skill: str
    title: str

    @classmethod
    def build(cls, assessment: Assessment) -> "AssessmentSummary":
        return cls(id=assessment.id, skill=assessment.skill.name, title=assessment.title)


class QuestionOut(BaseModel):
    id: int
    position: int
    prompt: str
    options: list[str]


class AssessmentDetail(AssessmentSummary):
    pass_mark: int = PASS_MARK
    questions: list[QuestionOut]

    @classmethod
    def build(cls, assessment: Assessment) -> "AssessmentDetail":
        return cls(
            id=assessment.id,
            skill=assessment.skill.name,
            title=assessment.title,
            questions=[
                QuestionOut(id=q.id, position=q.position, prompt=q.prompt, options=q.options)
                for q in assessment.questions
            ],
        )


class AttemptIn(BaseModel):
    answers: list[int] = Field(min_length=1, max_length=100)


class AttemptOut(BaseModel):
    id: int
    assessment_id: int
    skill: str
    score: int
    correct_count: int
    total: int
    passed: bool
    pass_mark: int = PASS_MARK
    verified: bool
    newly_verified: bool
    created_at: datetime

    @classmethod
    def build(
        cls, attempt: AssessmentAttempt, skill: str, verified: bool, newly_verified: bool
    ) -> "AttemptOut":
        return cls(
            id=attempt.id,
            assessment_id=attempt.assessment_id,
            skill=skill,
            score=attempt.score,
            correct_count=attempt.correct_count,
            total=attempt.total,
            passed=attempt.passed,
            verified=verified,
            newly_verified=newly_verified,
            created_at=attempt.created_at,
        )
