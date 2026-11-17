from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import NotFound, RuleViolation
from app.models import Assessment, AssessmentAttempt, Question, User, UserSkill
from app.models.enums import SkillKind
from app.services import rewards
from app.services.rules import PASS_MARK, POINTS_VERIFY_SKILL


@dataclass(frozen=True)
class ScoreResult:
    correct: int
    total: int
    score: int
    passed: bool


def score_answers(questions: list[Question], answers: list[int]) -> ScoreResult:
    total = len(questions)
    correct = sum(1 for q, a in zip(questions, answers, strict=True) if q.correct_index == a)
    score = (correct * 100 * 2 + total) // (total * 2)
    passed = correct * 100 >= PASS_MARK * total
    return ScoreResult(correct=correct, total=total, score=score, passed=passed)


def list_assessments(db: Session) -> list[Assessment]:
    stmt = select(Assessment).options(selectinload(Assessment.skill)).order_by(Assessment.id)
    return list(db.scalars(stmt))


def get_assessment(db: Session, assessment_id: int) -> Assessment:
    stmt = (
        select(Assessment)
        .where(Assessment.id == assessment_id)
        .options(selectinload(Assessment.skill), selectinload(Assessment.questions))
    )
    assessment = db.scalar(stmt)
    if assessment is None:
        raise NotFound("Assessment not found")
    return assessment


def submit_attempt(
    db: Session, user: User, assessment_id: int, answers: list[int]
) -> tuple[AssessmentAttempt, bool, bool]:
    assessment = get_assessment(db, assessment_id)
    link = db.scalar(
        select(UserSkill).where(
            UserSkill.user_id == user.id,
            UserSkill.skill_id == assessment.skill_id,
            UserSkill.kind == SkillKind.TEACH,
        )
    )
    if link is None:
        raise RuleViolation("Add this skill to your teaching list before taking its assessment")

    questions = assessment.questions
    if len(answers) != len(questions):
        raise RuleViolation(f"Expected {len(questions)} answers, received {len(answers)}")
    for question, answer in zip(questions, answers, strict=True):
        if not 0 <= answer < len(question.options):
            raise RuleViolation(f"Answer {answer} is out of range for question {question.position}")

    result = score_answers(questions, answers)
    attempt = AssessmentAttempt(
        user_id=user.id,
        assessment_id=assessment.id,
        answers=answers,
        correct_count=result.correct,
        total=result.total,
        score=result.score,
        passed=result.passed,
    )
    db.add(attempt)

    newly_verified = result.passed and not link.verified
    if newly_verified:
        link.verified = True
        rewards.award_points(user, POINTS_VERIFY_SKILL)
        rewards.grant_badge(db, user, rewards.Badge.VERIFIED_TEACHER)
    db.commit()
    return attempt, link.verified, newly_verified


def attempts_for(db: Session, user: User, limit: int, offset: int) -> list[AssessmentAttempt]:
    stmt = (
        select(AssessmentAttempt)
        .where(AssessmentAttempt.user_id == user.id)
        .options(selectinload(AssessmentAttempt.assessment).selectinload(Assessment.skill))
        .order_by(AssessmentAttempt.created_at.desc(), AssessmentAttempt.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt))
