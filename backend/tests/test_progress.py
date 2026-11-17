import pytest

from app.services.progress import level_for


@pytest.mark.parametrize(("points", "level"), [(0, 1), (99, 1), (100, 2), (240, 3), (420, 5)])
def test_level_thresholds(points, level):
    assert level_for(points) == level


def test_progress_summary(make_account):
    account = make_account()
    account.set_skills(teach=["Figma"], learn=["Python", "Spanish"])
    body = account.get("/users/me/progress").json()
    assert body["points"] == 0
    assert body["level"] == 1
    assert body["points_to_next_level"] == 100
    assert body["learning_goals"] == ["Python", "Spanish"]
    assert body["achievements"] == []


def test_skills_endpoint_requires_auth_and_searches(client, make_account):
    assert client.get("/skills").status_code == 401
    account = make_account()
    account.set_skills(teach=["Photography", "Python"], learn=["Public speaking"])
    names = [s["name"] for s in account.get("/skills", params={"q": "p"}).json()]
    assert names == ["Photography", "Public speaking", "Python"]
