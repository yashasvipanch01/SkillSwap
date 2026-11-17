from datetime import UTC, datetime, timedelta


def in_days(days: int) -> str:
    return (datetime.now(UTC) + timedelta(days=days)).isoformat()


def test_create_list_and_complete_session(accepted_exchange):
    learner, teacher, exchange_id = accepted_exchange()
    created = learner.post(
        f"/exchanges/{exchange_id}/sessions",
        {"title": "Intro", "objective": "Variables", "scheduled_at": in_days(2)},
    )
    assert created.status_code == 201
    session = created.json()
    assert session["status"] == "scheduled"

    later = teacher.post(
        f"/exchanges/{exchange_id}/sessions", {"title": "Loops", "scheduled_at": in_days(5)}
    ).json()
    listing = learner.get(f"/exchanges/{exchange_id}/sessions").json()
    assert [s["id"] for s in listing] == [session["id"], later["id"]]

    done = teacher.post(f"/sessions/{session['id']}/complete")
    assert done.status_code == 200
    assert done.json()["status"] == "completed"
    assert learner.post(f"/sessions/{session['id']}/complete").status_code == 409
    assert learner.get("/users/me/progress").json()["completed_sessions"] == 1


def test_session_validation(accepted_exchange):
    learner, _, exchange_id = accepted_exchange()
    url = f"/exchanges/{exchange_id}/sessions"
    assert learner.post(url, {"title": "Past", "scheduled_at": in_days(-1)}).status_code == 422
    assert learner.post(url, {"title": "", "scheduled_at": in_days(1)}).status_code == 422
    assert learner.post(url, {"title": "No date"}).status_code == 422


def test_sessions_require_an_accepted_exchange(make_account):
    learner = make_account("Learner")
    teacher = make_account("Teacher")
    teacher.set_skills(teach=["Python"], learn=[])
    exchange_id = learner.post("/exchanges", {"partner_id": teacher.id, "topic": "Python"}).json()["id"]
    response = learner.post(
        f"/exchanges/{exchange_id}/sessions", {"title": "Too early", "scheduled_at": in_days(1)}
    )
    assert response.status_code == 422


def test_session_is_private_to_participants(accepted_exchange, make_account):
    learner, _, exchange_id = accepted_exchange()
    session_id = learner.post(
        f"/exchanges/{exchange_id}/sessions", {"title": "Intro", "scheduled_at": in_days(1)}
    ).json()["id"]
    outsider = make_account("Outsider")
    assert outsider.post(f"/sessions/{session_id}/complete").status_code == 404
    assert outsider.post(
        f"/exchanges/{exchange_id}/sessions", {"title": "x", "scheduled_at": in_days(1)}
    ).status_code == 404
    assert learner.post("/sessions/9999/complete").status_code == 404


def complete(learner, teacher, exchange_id):
    assert learner.post(f"/exchanges/{exchange_id}/complete").status_code == 200


def test_review_requires_completed_exchange(accepted_exchange):
    learner, _, exchange_id = accepted_exchange()
    response = learner.post(f"/exchanges/{exchange_id}/reviews", {"rating": 5})
    assert response.status_code == 422


def test_review_flow_updates_rating_and_points(accepted_exchange):
    learner, teacher, exchange_id = accepted_exchange()
    complete(learner, teacher, exchange_id)

    created = learner.post(
        f"/exchanges/{exchange_id}/reviews", {"rating": 4, "comment": "Great teacher"}
    )
    assert created.status_code == 201
    assert created.json()["reviewer"]["name"] == "Learner"

    assert learner.post(f"/exchanges/{exchange_id}/reviews", {"rating": 5}).status_code == 409
    teacher.post(f"/exchanges/{exchange_id}/reviews", {"rating": 5})

    profile = learner.get(f"/users/{teacher.id}").json()
    assert profile["rating"] == 4.0
    assert profile["rating_count"] == 1
    reviews = learner.get(f"/users/{teacher.id}/reviews").json()
    assert [r["comment"] for r in reviews] == ["Great teacher"]
    assert learner.get("/users/me").json()["points"] == 50 + 10


def test_review_rating_bounds(accepted_exchange):
    learner, teacher, exchange_id = accepted_exchange()
    complete(learner, teacher, exchange_id)
    for rating in (0, 6, -1):
        assert learner.post(f"/exchanges/{exchange_id}/reviews", {"rating": rating}).status_code == 422


def test_outsider_cannot_review(accepted_exchange, make_account):
    learner, teacher, exchange_id = accepted_exchange()
    complete(learner, teacher, exchange_id)
    outsider = make_account("Outsider")
    assert outsider.post(f"/exchanges/{exchange_id}/reviews", {"rating": 1}).status_code == 404


def test_highly_rated_badge_after_three_strong_reviews(make_account):
    teacher = make_account("Teacher")
    teacher.set_skills(teach=["Python"], learn=[])
    for n in range(3):
        learner = make_account(f"Learner {n}")
        exchange_id = learner.post(
            "/exchanges", {"partner_id": teacher.id, "topic": "Python"}
        ).json()["id"]
        teacher.post(f"/exchanges/{exchange_id}/accept")
        learner.post(f"/exchanges/{exchange_id}/complete")
        assert learner.post(f"/exchanges/{exchange_id}/reviews", {"rating": 5}).status_code == 201

    codes = {a["code"] for a in teacher.get("/users/me/progress").json()["achievements"]}
    assert "highly_rated" in codes
