from typing import Annotated

import jwt
from fastapi import Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import Unauthorized
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import User
from app.services.users import get_user

bearer_scheme = HTTPBearer(auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if credentials is None:
        raise Unauthorized("Not authenticated")
    try:
        user_id = decode_access_token(credentials.credentials)
    except (jwt.PyJWTError, KeyError, ValueError):
        raise Unauthorized("Invalid or expired token") from None
    try:
        return get_user(db, user_id)
    except Exception:
        raise Unauthorized("Invalid or expired token") from None


CurrentUser = Annotated[User, Depends(get_current_user)]
Limit = Annotated[int, Query(ge=1, le=100)]
Offset = Annotated[int, Query(ge=0)]
