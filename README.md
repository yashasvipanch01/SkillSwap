# SkillSwap

SkillSwap is a peer-to-peer skill exchange platform. People teach what they know and learn what they want, with skills as the currency instead of money. A learner finds a partner who teaches the skill they want, proposes an exchange, schedules sessions with a video call link, and both sides leave reviews.

The repository has two parts:

| Folder | What it is |
| --- | --- |
| `backend/` | REST API built with FastAPI, SQLAlchemy and Alembic |
| `frontend/` | Next.js web app that talks to the API |

## Features

- **Accounts:** sign up and log in with JWT authentication, passwords stored as bcrypt hashes.
- **Profiles:** bio, skills to teach, skills to learn (custom skills allowed).
- **Skill verification:** a teaching skill becomes verified only with a score of 75% or more in a test. The test is graded on the server, and correct answers are never sent to the browser.
- **Matching:** partners are ranked with a simple, explainable score (40 points for teaching what you want, 30 for wanting what you teach, plus shared availability and learning style, capped at 100). Three-person exchange circles are detected too.
- **Exchanges:** a request moves through `pending`, `accepted` and `completed` (or `rejected` and `cancelled`). A table defines who may do which move, and wrong moves are refused.
- **Learning sessions:** schedule sessions inside an accepted exchange. Each session gets its own video call link (Jitsi Meet).
- **Reviews, points and badges:** ratings from 1 to 5 after a completed exchange, points for activity, levels, and badges such as *Verified teacher*.

## Tech stack

| Area | Tools |
| --- | --- |
| Backend | Python, FastAPI, SQLAlchemy 2, Alembic, Pydantic, PyJWT, bcrypt |
| Database | SQLite for development, PostgreSQL ready through Docker |
| Frontend | Next.js, React, TypeScript, Tailwind CSS |
| Quality | pytest (68 tests), ruff, Docker, GitHub Actions |

## How it works

```
Browser (Next.js)  --JSON over HTTP-->  FastAPI routers  ->  services (business rules)  ->  SQLAlchemy models  ->  database
```

Routers stay thin, the rules live in services that know nothing about HTTP, and the database also enforces important rules with constraints (for example, one review per person per exchange).

## Run it locally

You need Python 3.11 or newer and Node.js 20 or newer. Run the backend and the frontend in two terminals.

**Backend**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Mac/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
copy .env.example .env          # Mac/Linux: cp .env.example .env
alembic upgrade head
python -m app.seed              # optional demo data
uvicorn app.main:app --reload
```

The API runs at http://127.0.0.1:8000 and the interactive documentation is at http://127.0.0.1:8000/docs.

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. The frontend expects the API at `http://127.0.0.1:8000`. You can change this with the `NEXT_PUBLIC_API_URL` environment variable.

**Demo accounts** (password `skillswap`): `amara@example.com`, `yashwini@example.com`, `rahul@example.com`, `sofia@example.com`, `jordan@example.com`, `nikhil@example.com`.

Reset the demo data at any time with `python -m app.seed --reset`. Your data is stored in `backend/skillswap.db`.

## Tests

```bash
cd backend
python -m pytest
ruff check .
```

The tests run against an in-memory database, so they need no setup.

## Project structure

```
backend/
  app/
    core/        settings, security, domain errors
    db/          database engine and session
    models/      database tables
    schemas/     request and response validation
    services/    business rules
    routers/     API endpoints
    seed.py      demo data
  migrations/    Alembic migrations
  tests/         pytest suite
  docs/          build guide and interview notes
frontend/
  app/           Next.js pages
  components/    screens and UI
  lib/api.ts     API client
```

More detail about the API, endpoints and business rules is in [`backend/README.md`](backend/README.md).

## Known limitations

- Access tokens only: no refresh tokens, email verification or login rate limiting.
- Exchange circles are detected but not saved or confirmed by all members yet.
- Video call rooms use the public Jitsi Meet service and are protected only by an unguessable link.
- Matching scans all users in Python, which is fine for thousands of users but not for millions.
- Chat and file sharing are not included.

## Ideas for the future

- Save exchange circles with a confirmation step from every member.
- Chat between exchange partners.
- Refresh tokens and login rate limiting.
- Deploy to a cloud host with a managed PostgreSQL database.

## Credits

The backend, the API connection and the video call feature were built by Yashasvi Panchal. The original frontend design was created by a friend.
