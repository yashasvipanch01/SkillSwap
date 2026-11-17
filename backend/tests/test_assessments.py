import pytest

from app.models import Question
from app.services.assessments import score_answers


def make_questions(n: int, correct: int = 0) -> list[Question]:
    return [Question(position=i, prompt="q", options=["a", "b"], correct_index=correct) for i in range(n)]


@pytest.mark.parametrize(
    ("correct", "total", "score", "passed"),
    [(4, 4, 100, True), (3, 4, 75, True), (2, 4, 50, False), (0, 4, 0, False), (5, 7, 71, False), (6, 8, 75, True)],
)
def test_score_and_pass_mark(correct, total, score, passed):
    questions = make_questions(total)
    answers = [0] * correct + [1] * (total - correct)
    result = score_answers(questions, answers)
    assert (result.score, result.passed) == (score, passed)


def test_pass_decision_uses_exact_arithmetic_not_rounded_score():
    questions = make_questions(200)
    answers = [0] * 149 + [1] * 51
    result = score_answers(questions, answers)
    assert result.score == 75
    assert result.passed is False


def test_questions_do_not_expose_answers(make_account, seed_assessment):
    account = make_account()
    assessment_id = seed_assessment()
    body = account.get(f"/assessments/{assessment_id}").json()
    assert body["pass_mark"] == 75
    assert len(body["questions"]) == 4
    assert "correct_index" not in str(body)


def test_passing_attempt_verifies_skill_and_awards_points(make_account, seed_assessment):
    account = make_account()
    account.set_skills(teach=["Python"], learn=[])
    assessment_id = seed_assessment("Python", correct=(1, 1, 1, 1))

    response = account.post(f"/assessments/{assessment_id}/attempts", {"answers": [1, 1, 1, 0]})
    assert response.status_code == 201
    body = response.json()
    assert body["score"] == 75
    assert body["passed"] and body["verified"] and body["newly_verified"]

    me = account.get("/users/me").json()
    assert me["verified"] == ["Python"]
    assert me["points"] == 30
    badges = [a["code"] for a in account.get("/users/me/progress").json()["achievements"]]
    assert badges == ["verified_teacher"]


def test_failing_attempt_does_not_verify(make_account, seed_assessment):
    account = make_account()
    account.set_skills(teach=["Python"], learn=[])
    assessment_id = seed_assessment("Python")

    body = account.post(f"/assessments/{assessment_id}/attempts", {"answers": [1, 1, 0, 0]}).json()
    assert body["score"] == 50
    assert body["passed"] is False and body["verified"] is False
    assert account.get("/users/me").json()["verified"] == []


def test_retake_after_failure_can_verify_and_points_are_awarded_once(make_account, seed_assessment):
    account = make_account()
    account.set_skills(teach=["Python"], learn=[])
    assessment_id = seed_assessment("Python")
    url = f"/assessments/{assessment_id}/attempts"

    assert account.post(url, {"answers": [0, 0, 0, 0]}).json()["verified"] is False
    assert account.post(url, {"answers": [1, 1, 1, 1]}).json()["newly_verified"] is True
    again = account.post(url, {"answers": [1, 1, 1, 1]}).json()
    assert again["newly_verified"] is False
    assert account.get("/users/me").json()["points"] == 30
    assert len(account.get("/users/me/attempts").json()) == 3


def test_failed_retake_does_not_remove_verification(make_account, seed_assessment):
    account = make_account()
    account.set_skills(teach=["Python"], learn=[])
    assessment_id = seed_assessment("Python")
    url = f"/assessments/{assessment_id}/attempts"
    account.post(url, {"answers": [1, 1, 1, 1]})
    account.post(url, {"answers": [0, 0, 0, 0]})
    assert account.get("/users/me").json()["verified"] == ["Python"]


def test_cannot_take_assessment_for_skill_you_do_not_teach(make_account, seed_assessment):
    account = make_account()
    account.set_skills(teach=["Figma"], learn=["Python"])
    assessment_id = seed_assessment("Python")
    response = account.post(f"/assessments/{assessment_id}/attempts", {"answers": [1, 1, 1, 1]})
    assert response.status_code == 422


def test_answer_validation(make_account, seed_assessment):
    account = make_account()
    account.set_skills(teach=["Python"], learn=[])
    url = f"/assessments/{seed_assessment('Python')}/attempts"
    assert account.post(url, {"answers": [1, 1]}).status_code == 422
    assert account.post(url, {"answers": [1, 1, 1, 9]}).status_code == 422
    assert account.post(url, {"answers": [1, 1, 1, -1]}).status_code == 422
    assert account.post(url, {"answers": []}).status_code == 422
    assert account.post("/assessments/999/attempts", {"answers": [1]}).status_code == 404


def test_replacing_skills_keeps_verified_status_for_kept_skills(
    make_account, seed_assessment
):
    account = make_account()
    account.set_skills(teach=["Python", "Figma"], learn=[])
    assessment_id = seed_assessment("Python")
    assert account.post(f"/assessments/{assessment_id}/attempts", {"answers": [1, 1, 1, 1]}).status_code == 201

    body = account.set_skills(teach=["Python"], learn=["Spanish"])
    assert body["verified"] == ["Python"]
