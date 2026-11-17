from fastapi import APIRouter, status

from app.core.security import create_access_token
from app.deps import DbSession
from app.schemas.user import LoginIn, MeOut, RegisterIn, TokenOut
from app.services import users

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_response(user) -> TokenOut:
    return TokenOut(access_token=create_access_token(user.id), user=MeOut.build(user))


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterIn, db: DbSession):
    user = users.register(db, payload.name, payload.email, payload.password)
    return _token_response(user)


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: DbSession):
    user = users.authenticate(db, payload.email, payload.password)
    return _token_response(users.get_user(db, user.id))
