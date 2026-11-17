from fastapi import APIRouter, status

from app.deps import CurrentUser, DbSession
from app.schemas.assessment import (
    AssessmentDetail,
    AssessmentSummary,
    AttemptIn,
    AttemptOut,
)
from app.services import assessments

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.get("", response_model=list[AssessmentSummary])
def list_assessments(_: CurrentUser, db: DbSession):
    return [AssessmentSummary.build(a) for a in assessments.list_assessments(db)]


@router.get("/{assessment_id}", response_model=AssessmentDetail)
def read_assessment(assessment_id: int, _: CurrentUser, db: DbSession):
    return AssessmentDetail.build(assessments.get_assessment(db, assessment_id))


@router.post("/{assessment_id}/attempts", response_model=AttemptOut, status_code=status.HTTP_201_CREATED)
def submit_attempt(assessment_id: int, payload: AttemptIn, user: CurrentUser, db: DbSession):
    attempt, verified, newly_verified = assessments.submit_attempt(
        db, user, assessment_id, payload.answers
    )
    return AttemptOut.build(attempt, attempt.assessment.skill.name, verified, newly_verified)
