from fastapi import APIRouter, status

from app.deps import CurrentUser, DbSession, Limit, Offset
from app.models.enums import ExchangeStatus
from app.schemas.exchange import (
    ExchangeIn,
    ExchangeOut,
    ReviewIn,
    ReviewOut,
    SessionIn,
    SessionOut,
)
from app.services import exchanges, reviews, sessions
from app.services.exchanges import Action

router = APIRouter(tags=["exchanges"])


@router.post("/exchanges", response_model=ExchangeOut, status_code=status.HTTP_201_CREATED)
def create_exchange(payload: ExchangeIn, user: CurrentUser, db: DbSession):
    exchange = exchanges.create_exchange(db, user, payload.partner_id, payload.topic, payload.note)
    return ExchangeOut.build(exchange, user.id)


@router.get("/exchanges", response_model=list[ExchangeOut])
def list_exchanges(
    user: CurrentUser,
    db: DbSession,
    status: ExchangeStatus | None = None,
    limit: Limit = 20,
    offset: Offset = 0,
):
    return [
        ExchangeOut.build(e, user.id)
        for e in exchanges.list_exchanges(db, user, status, limit, offset)
    ]


@router.get("/exchanges/{exchange_id}", response_model=ExchangeOut)
def read_exchange(exchange_id: int, user: CurrentUser, db: DbSession):
    return ExchangeOut.build(exchanges.get_for_participant(db, user, exchange_id), user.id)


def _transition(action: Action):
    def handler(exchange_id: int, user: CurrentUser, db: DbSession) -> ExchangeOut:
        return ExchangeOut.build(exchanges.apply_action(db, user, exchange_id, action), user.id)

    handler.__name__ = f"{action.value}_exchange"
    return handler


for _action in Action:
    router.add_api_route(
        f"/exchanges/{{exchange_id}}/{_action.value}",
        _transition(_action),
        methods=["POST"],
        response_model=ExchangeOut,
        summary=f"{_action.value.capitalize()} an exchange",
    )


@router.post(
    "/exchanges/{exchange_id}/sessions",
    response_model=SessionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_session(exchange_id: int, payload: SessionIn, user: CurrentUser, db: DbSession):
    session = sessions.create_session(
        db, user, exchange_id, payload.title, payload.objective, payload.scheduled_at
    )
    return SessionOut.build(session)


@router.get("/exchanges/{exchange_id}/sessions", response_model=list[SessionOut])
def list_sessions(exchange_id: int, user: CurrentUser, db: DbSession):
    return [SessionOut.build(s) for s in sessions.list_sessions(db, user, exchange_id)]


@router.post("/sessions/{session_id}/complete", response_model=SessionOut)
def complete_session(session_id: int, user: CurrentUser, db: DbSession):
    return SessionOut.build(sessions.complete_session(db, user, session_id))


@router.post(
    "/exchanges/{exchange_id}/reviews", response_model=ReviewOut, status_code=status.HTTP_201_CREATED
)
def create_review(exchange_id: int, payload: ReviewIn, user: CurrentUser, db: DbSession):
    review = reviews.create_review(db, user, exchange_id, payload.rating, payload.comment)
    return ReviewOut.build(review)
