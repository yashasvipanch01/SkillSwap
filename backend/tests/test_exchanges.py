import pytest


@pytest.fixture
def pair(make_account):
    learner = make_account("Learner")
    teacher = make_account("Teacher")
    teacher.set_skills(teach=["Python"], learn=["Figma"])
    learner.set_skills(teach=["Figma"], learn=["Python"])
    return learner, teacher


def propose(learner, teacher, topic="Python"):
    return learner.post("/exchanges", {"partner_id": teacher.id, "topic": topic, "note": "Hello"})


def test_create_exchange(pair):
    learner, teacher = pair
    response = propose(learner, teacher)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert body["topic"] == "Python"
    assert body["role"] == "requester"
    assert body["person"]["name"] == "Teacher"

    seen_by_partner = teacher.get(f"/exchanges/{body['id']}").json()
    assert seen_by_partner["role"] == "partner"
    assert seen_by_partner["person"]["name"] == "Learner"


def test_cannot_exchange_with_yourself(pair):
    learner, _ = pair
    response = learner.post("/exchanges", {"partner_id": learner.id, "topic": "Figma"})
    assert response.status_code == 422


def test_partner_must_teach_the_topic(pair):
    learner, teacher = pair
    assert propose(learner, teacher, topic="Cooking").status_code == 422
    assert propose(learner, teacher, topic="Figma").status_code == 422


def test_unknown_partner(pair):
    learner, _ = pair
    assert learner.post("/exchanges", {"partner_id": 9999, "topic": "Python"}).status_code == 404


def test_duplicate_open_exchange_is_a_conflict_but_reopening_after_close_is_fine(pair):
    learner, teacher = pair
    first = propose(learner, teacher).json()
    assert propose(learner, teacher).status_code == 409
    assert learner.post(f"/exchanges/{first['id']}/cancel").status_code == 200
    assert propose(learner, teacher).status_code == 201


def test_only_the_partner_can_accept_or_reject(pair):
    learner, teacher = pair
    exchange_id = propose(learner, teacher).json()["id"]
    assert learner.post(f"/exchanges/{exchange_id}/accept").status_code == 403
    assert learner.post(f"/exchanges/{exchange_id}/reject").status_code == 403
    accepted = teacher.post(f"/exchanges/{exchange_id}/accept")
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "accepted"


def test_reject_is_terminal(pair):
    learner, teacher = pair
    exchange_id = propose(learner, teacher).json()["id"]
    assert teacher.post(f"/exchanges/{exchange_id}/reject").json()["status"] == "rejected"
    for action in ("accept", "cancel", "complete", "reject"):
        assert teacher.post(f"/exchanges/{exchange_id}/{action}").status_code == 409


def test_cannot_complete_before_acceptance(pair):
    learner, teacher = pair
    exchange_id = propose(learner, teacher).json()["id"]
    assert learner.post(f"/exchanges/{exchange_id}/complete").status_code == 409
    assert teacher.post(f"/exchanges/{exchange_id}/complete").status_code == 409


def test_complete_awards_points_and_badge_to_both(pair):
    learner, teacher = pair
    exchange_id = propose(learner, teacher).json()["id"]
    teacher.post(f"/exchanges/{exchange_id}/accept")
    done = learner.post(f"/exchanges/{exchange_id}/complete").json()
    assert done["status"] == "completed"
    assert done["completed_at"] is not None

    for account in (learner, teacher):
        progress = account.get("/users/me/progress").json()
        assert progress["points"] == 50
        assert progress["completed_exchanges"] == 1
        assert [a["code"] for a in progress["achievements"]] == ["first_exchange"]

    assert teacher.post(f"/exchanges/{exchange_id}/complete").status_code == 409
    assert learner.get("/users/me").json()["points"] == 50


def test_either_participant_can_cancel_an_accepted_exchange(pair):
    learner, teacher = pair
    exchange_id = propose(learner, teacher).json()["id"]
    teacher.post(f"/exchanges/{exchange_id}/accept")
    assert teacher.post(f"/exchanges/{exchange_id}/cancel").json()["status"] == "cancelled"


def test_outsiders_cannot_see_or_change_an_exchange(pair, make_account):
    learner, teacher = pair
    outsider = make_account("Outsider")
    exchange_id = propose(learner, teacher).json()["id"]
    assert outsider.get(f"/exchanges/{exchange_id}").status_code == 404
    assert outsider.post(f"/exchanges/{exchange_id}/accept").status_code == 404
    assert outsider.post(f"/exchanges/{exchange_id}/cancel").status_code == 404
    assert outsider.get("/exchanges").json() == []
    assert outsider.get(f"/exchanges/{exchange_id}/sessions").status_code == 404


def test_list_filters_and_pagination(pair):
    learner, teacher = pair
    first = propose(learner, teacher).json()["id"]
    teacher.post(f"/exchanges/{first}/accept")
    teacher.set_skills(teach=["Python", "Spanish"], learn=["Figma"])
    second = learner.post("/exchanges", {"partner_id": teacher.id, "topic": "Spanish"}).json()["id"]

    everything = learner.get("/exchanges").json()
    assert [e["id"] for e in everything] == [second, first]
    assert [e["id"] for e in learner.get("/exchanges", params={"status": "accepted"}).json()] == [first]
    assert len(learner.get("/exchanges", params={"limit": 1}).json()) == 1
    assert learner.get("/exchanges", params={"status": "bogus"}).status_code == 422
    assert len(teacher.get("/exchanges").json()) == 2


def test_unauthenticated_requests_are_rejected(client):
    assert client.get("/exchanges").status_code == 401
    assert client.post("/exchanges", json={"partner_id": 1, "topic": "x"}).status_code == 401
