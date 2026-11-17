import os

os.environ["BCRYPT_ROUNDS"] = "4"
os.environ["SECRET_KEY"] = "test-secret-that-is-long-enough-for-hs256-signing"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import get_db
from app.main import app


@pytest.fixture
def session_factory():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    engine.dispose()


@pytest.fixture
def db(session_factory):
    with session_factory() as session:
        yield session


@pytest.fixture
def client(session_factory):
    def override_get_db():
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


class Account:
    def __init__(self, client: TestClient, name: str, email: str, password: str = "secret123"):
        response = client.post(
            "/auth/register", json={"name": name, "email": email, "password": password}
        )
        assert response.status_code == 201, response.text
        body = response.json()
        self.client = client
        self.id = body["user"]["id"]
        self.headers = {"Authorization": f"Bearer {body['access_token']}"}

    def get(self, url, **kwargs):
        return self.client.get(url, headers=self.headers, **kwargs)

    def post(self, url, json=None):
        return self.client.post(url, headers=self.headers, json=json)

    def put(self, url, json=None):
        return self.client.put(url, headers=self.headers, json=json)

    def patch(self, url, json=None):
        return self.client.patch(url, headers=self.headers, json=json)

    def set_skills(self, teach, learn):
        response = self.put("/users/me/skills", {"teach": teach, "learn": learn})
        assert response.status_code == 200, response.text
        return response.json()


@pytest.fixture
def make_account(client):
    counter = iter(range(1, 1000))

    def factory(name: str = "Test User", **kwargs) -> Account:
        n = next(counter)
        return Account(client, name, kwargs.pop("email", f"user{n}@example.com"), **kwargs)

    return factory


@pytest.fixture
def seed_assessment(db):
    from app.models import Assessment, Question
    from app.services.skills import get_or_create_skills

    def factory(skill_name: str = "Python", correct: tuple[int, ...] = (1, 1, 1, 1)) -> int:
        skill = get_or_create_skills(db, [skill_name])[skill_name.casefold()]
        assessment = Assessment(skill_id=skill.id, title=f"{skill_name} test")
        for position, answer in enumerate(correct, start=1):
            assessment.questions.append(
                Question(
                    position=position,
                    prompt=f"Question {position}",
                    options=["A", "B", "C", "D"],
                    correct_index=answer,
                )
            )
        db.add(assessment)
        db.commit()
        return assessment.id

    return factory


@pytest.fixture
def accepted_exchange(make_account):
    def factory():
        learner = make_account("Learner")
        teacher = make_account("Teacher")
        teacher.set_skills(teach=["Python"], learn=["Figma"])
        learner.set_skills(teach=["Figma"], learn=["Python"])
        created = learner.post(
            "/exchanges", {"partner_id": teacher.id, "topic": "Python", "note": "Hi"}
        ).json()
        teacher.post(f"/exchanges/{created['id']}/accept")
        return learner, teacher, created["id"]

    return factory
