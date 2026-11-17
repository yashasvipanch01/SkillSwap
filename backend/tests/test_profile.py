import jwt


def test_update_profile_fields(make_account):
    account = make_account("Ada Lovelace")
    response = account.patch(
        "/users/me",
        {
            "bio": "Mathematician",
            "availability": ["Weekends", "weekends", " Evenings "],
            "preferences": ["Project-based"],
            "username": "ada_l",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["bio"] == "Mathematician"
    assert body["availability"] == ["Weekends", "Evenings"]
    assert body["username"] == "@ada_l"


def test_username_must_be_unique_and_well_formed(make_account):
    first = make_account("First")
    second = make_account("Second")
    taken = first.get("/users/me").json()["username"]
    assert second.patch("/users/me", {"username": taken}).status_code == 409
    assert second.patch("/users/me", {"username": "no spaces"}).status_code == 422
    assert second.patch("/users/me", {"username": "ab"}).status_code == 422


def test_profile_update_rejects_unknown_fields(make_account):
    account = make_account()
    assert account.patch("/users/me", {"points": 9999}).status_code == 422
    assert account.patch("/users/me", {"email": "x@example.com"}).status_code == 422


def test_set_skills_creates_normalises_and_marks_onboarding(make_account):
    account = make_account()
    body = account.set_skills(teach=["  UI/UX   Design ", "figma"], learn=["Python", "python"])
    assert body["teach"] == ["UI/UX Design", "figma"]
    assert body["learn"] == ["Python"]
    assert body["onboarding_complete"] is True


def test_skill_names_are_shared_case_insensitively(make_account):
    first = make_account()
    second = make_account()
    first.set_skills(teach=["Python"], learn=[])
    second.set_skills(teach=["PYTHON"], learn=[])
    names = [s["name"] for s in first.get("/skills", params={"q": "pyth"}).json()]
    assert names == ["Python"]


def test_skill_cannot_be_taught_and_learned(make_account):
    account = make_account()
    response = account.put("/users/me/skills", {"teach": ["Python"], "learn": ["python"]})
    assert response.status_code == 422


def test_public_profile_hides_email(make_account):
    viewer = make_account()
    other = make_account("Other Person")
    body = viewer.get(f"/users/{other.id}").json()
    assert "email" not in body
    assert body["name"] == "Other Person"
    assert viewer.get("/users/99999").status_code == 404


def test_protected_routes_require_a_valid_token(client, make_account):
    assert client.get("/users/me").status_code == 401
    assert client.get("/users/me", headers={"Authorization": "Bearer garbage"}).status_code == 401
    forged = jwt.encode({"sub": "1"}, "another-secret-that-is-long-enough-for-hs256", algorithm="HS256")
    assert client.get("/users/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401

    account = make_account()
    assert account.get("/users/me").status_code == 200


def test_token_for_deleted_user_is_rejected(client, db, make_account):
    from app.models import User

    account = make_account()
    db.delete(db.get(User, account.id))
    db.commit()
    assert account.get("/users/me").status_code == 401
