def test_register_returns_token_and_profile(client):
    response = client.post(
        "/auth/register",
        json={"name": "Amara Morgan", "email": "Amara@Example.com", "password": "secret123"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "amara@example.com"
    assert body["user"]["username"] == "@amaramorgan"
    assert body["user"]["initials"] == "AM"
    assert body["user"]["onboarding_complete"] is False
    assert "password" not in str(body)


def test_duplicate_email_is_rejected_case_insensitively(client):
    payload = {"name": "A", "email": "a@example.com", "password": "secret123"}
    assert client.post("/auth/register", json=payload).status_code == 201
    payload["email"] = "A@EXAMPLE.COM"
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 409


def test_usernames_are_made_unique(client):
    for n in range(3):
        response = client.post(
            "/auth/register",
            json={"name": "Sam Lee", "email": f"sam{n}@example.com", "password": "secret123"},
        )
        assert response.status_code == 201
    names = {
        client.post(
            "/auth/login", json={"email": f"sam{n}@example.com", "password": "secret123"}
        ).json()["user"]["username"]
        for n in range(3)
    }
    assert names == {"@samlee", "@samlee2", "@samlee3"}


def test_register_validation(client):
    cases = [
        {"name": "", "email": "a@example.com", "password": "secret123"},
        {"name": "A", "email": "not-an-email", "password": "secret123"},
        {"name": "A", "email": "a@example.com", "password": "short"},
        {"name": "   ", "email": "a@example.com", "password": "secret123"},
    ]
    for payload in cases:
        assert client.post("/auth/register", json=payload).status_code == 422


def test_login_success_and_failure(client):
    client.post(
        "/auth/register", json={"name": "A", "email": "a@example.com", "password": "secret123"}
    )
    ok = client.post("/auth/login", json={"email": "a@example.com", "password": "secret123"})
    assert ok.status_code == 200
    assert ok.json()["access_token"]

    wrong_password = client.post("/auth/login", json={"email": "a@example.com", "password": "nope123"})
    unknown_user = client.post("/auth/login", json={"email": "x@example.com", "password": "secret123"})
    assert wrong_password.status_code == unknown_user.status_code == 401
    assert wrong_password.json() == unknown_user.json()


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
