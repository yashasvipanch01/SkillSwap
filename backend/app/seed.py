import argparse
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.core.security import hash_password
from app.db.base import Base, utcnow
from app.db.session import SessionLocal, engine
from app.models import (
    Achievement,
    Assessment,
    Exchange,
    LearningSession,
    Question,
    Review,
    User,
    UserSkill,
)
from app.models.enums import ExchangeStatus, SessionStatus, SkillKind
from app.services.rewards import Badge
from app.services.skills import get_or_create_skills

DEMO_PASSWORD = "skillswap"

USERS = [
    dict(
        key="amara", name="Amara Morgan", username="@amaradesigns", email="amara@example.com",
        bio="Product designer learning to build thoughtful tools.",
        teach=["UI/UX Design", "Figma"], learn=["Python"], verified=[],
        preferences=["Project-based"], availability=["Saturday afternoons"], points=240,
    ),
    dict(
        key="yashwini", name="Yashwini Shinde", username="@yashwini", email="yashwini@example.com",
        bio="Final-year CS student exploring design and building products.",
        teach=["Spanish", "Public speaking"], learn=["Python", "UI/UX Design"], verified=[],
        preferences=["Project-based"], availability=["Saturday afternoons"], points=120,
    ),
    dict(
        key="rahul", name="Rahul Mehta", username="@rahulbuilds", email="rahul@example.com",
        bio="Backend developer who loves making APIs approachable.",
        teach=["Python", "FastAPI"], learn=["UI/UX Design"], verified=["Python"],
        preferences=["Project-based"], availability=["Saturday afternoons"], points=420,
    ),
    dict(
        key="sofia", name="Sofia Alvarez", username="@sofiawrites", email="sofia@example.com",
        bio="Product writer helping teams turn ideas into clear stories.",
        teach=["Product Writing"], learn=["Figma", "Prototyping"], verified=["Product Writing"],
        preferences=["Conversation-first"], availability=["Weekday evenings"], points=315,
    ),
    dict(
        key="jordan", name="Jordan Lee", username="@jordanframes", email="jordan@example.com",
        bio="Photographer exploring design systems and visual language.",
        teach=["Photography"], learn=["Design Systems"], verified=["Photography"],
        preferences=["Visual examples"], availability=["Saturday afternoons"], points=270,
    ),
    dict(
        key="nikhil", name="Nikhil Rao", username="@nikhilrao", email="nikhil@example.com",
        bio="Data analyst who wants to write about data more clearly.",
        teach=["Python"], learn=["Product Writing"], verified=[],
        preferences=["Conversation-first"], availability=["Weekday evenings"], points=60,
    ),
]

ASSESSMENTS = {
    "UI/UX Design": [
        ("Which principle keeps a design system consistent?",
         ["More colors", "Shared tokens and reusable components", "No documentation",
          "Every screen from scratch"], 1),
        ("What is the best first step when improving a confusing flow?",
         ["Add animation", "Increase font sizes", "Observe where people get stuck",
          "Hide actions"], 2),
        ("Strong interface hierarchy helps people…",
         ["Understand what to do next", "See more gradients", "Avoid scrolling",
          "Use smaller tap targets"], 0),
        ("Which artifact aligns a team early?",
         ["Finished logo", "User journey map", "Long changelog", "Color picker"], 1),
    ],
    "Python": [
        ("What does len([1, 2, 3]) return?", ["2", "3", "4", "It raises an error"], 1),
        ("Which built-in type is immutable?", ["list", "dict", "set", "tuple"], 3),
        ("What does a with statement manage?",
         ["Loops", "Setup and cleanup of a context", "Imports", "Type hints"], 1),
        ("What does bool([]) evaluate to?", ["True", "False", "None", "It raises an error"], 1),
    ],
    "Photography": [
        ("What does a lower f-number (wider aperture) do?",
         ["Admits more light and gives a shallower depth of field", "Admits less light",
          "Limits the maximum shutter speed", "Makes the image monochrome"], 0),
        ("Which setting mainly controls motion blur?",
         ["ISO", "Shutter speed", "White balance", "Lens coating"], 1),
        ("The rule of thirds helps with…", ["Exposure", "Composition", "Autofocus speed", "File size"], 1),
        ("Raising ISO mainly increases…",
         ["Sensor sensitivity and noise", "Lens sharpness", "Battery life", "Depth of field"], 0),
    ],
}


def reset_schema() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def seed(db: Session) -> None:
    if db.scalar(select(User.id).limit(1)):
        return

    password_hash = hash_password(DEMO_PASSWORD)
    users: dict[str, User] = {}
    for data in USERS:
        user = User(
            name=data["name"], username=data["username"], email=data["email"],
            password_hash=password_hash, bio=data["bio"], availability=data["availability"],
            preferences=data["preferences"], points=data["points"], onboarding_complete=True,
        )
        skills = get_or_create_skills(db, data["teach"] + data["learn"])
        verified = {name.casefold() for name in data["verified"]}
        for name in data["teach"]:
            skill = skills[name.casefold()]
            user.skills.append(
                UserSkill(skill=skill, kind=SkillKind.TEACH, verified=name.casefold() in verified)
            )
        for name in data["learn"]:
            user.skills.append(UserSkill(skill=skills[name.casefold()], kind=SkillKind.LEARN))
        db.add(user)
        users[data["key"]] = user
    db.flush()

    for skill_name, questions in ASSESSMENTS.items():
        skill = get_or_create_skills(db, [skill_name])[skill_name.casefold()]
        assessment = Assessment(skill_id=skill.id, title=f"{skill_name} fundamentals")
        for position, (prompt, options, correct) in enumerate(questions, start=1):
            assessment.questions.append(
                Question(position=position, prompt=prompt, options=options, correct_index=correct)
            )
        db.add(assessment)

    now = utcnow()

    def skill_of(name: str):
        return get_or_create_skills(db, [name])[name.casefold()]

    def exchange(requester, partner, topic, status, note, days_ago):
        record = Exchange(
            requester_id=users[requester].id, partner_id=users[partner].id,
            skill_id=skill_of(topic).id, status=status, note=note,
            created_at=now - timedelta(days=days_ago), updated_at=now - timedelta(days=days_ago),
            completed_at=now - timedelta(days=days_ago - 1) if status is ExchangeStatus.COMPLETED else None,
        )
        db.add(record)
        db.flush()
        return record

    done = exchange("yashwini", "rahul", "Python", ExchangeStatus.COMPLETED,
                    "Want to learn Python by building a small project.", 20)
    ongoing = exchange("yashwini", "amara", "UI/UX Design", ExchangeStatus.ACCEPTED,
                       "Would love feedback on my portfolio flow.", 5)
    figma = exchange("sofia", "amara", "Figma", ExchangeStatus.COMPLETED,
                     "Help me get comfortable with prototyping in Figma.", 30)
    exchange("jordan", "rahul", "FastAPI", ExchangeStatus.PENDING, "Curious how APIs are structured.", 1)

    db.add(LearningSession(
        exchange_id=ongoing.id, title="Portfolio walkthrough",
        objective="Review the onboarding flow together.",
        scheduled_at=now + timedelta(days=2), status=SessionStatus.SCHEDULED,
    ))

    reviews = [
        (done, "yashwini", "rahul", 5, "Patient and practical. Learned a lot."),
        (done, "rahul", "yashwini", 5, "Great questions, quick learner."),
        (figma, "sofia", "amara", 5, "Clear explanations and useful exercises."),
        (figma, "amara", "sofia", 4, "Thoughtful partner."),
    ]
    for record, reviewer, reviewee, rating, comment in reviews:
        db.add(Review(
            exchange_id=record.id, reviewer_id=users[reviewer].id,
            reviewee_id=users[reviewee].id, rating=rating, comment=comment,
        ))

    for key in ("rahul", "sofia", "jordan"):
        db.add(Achievement(user_id=users[key].id, code=Badge.VERIFIED_TEACHER.value))
    for key in ("yashwini", "rahul", "sofia", "amara"):
        db.add(Achievement(user_id=users[key].id, code=Badge.FIRST_EXCHANGE.value))
    db.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the SkillSwap demo data")
    parser.add_argument("--reset", action="store_true", help="drop and recreate all tables first")
    args = parser.parse_args()
    if args.reset:
        reset_schema()
    with SessionLocal() as db:
        seed(db)
    print("Demo data ready. Log in with any seeded email and the password 'skillswap'.")


if __name__ == "__main__":
    main()
