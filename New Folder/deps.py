import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.crud import user as user_crud
from app.db.session import get_db
from app.models.user import User

# auto_error=False lets us support optional auth (guest checkout) on some routes.
bearer_scheme = HTTPBearer(auto_error=False)

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials.",
    headers={"WWW-Authenticate": "Bearer"},
)


async def _resolve_user(
    credentials: HTTPAuthorizationCredentials | None, db: AsyncSession
) -> User | None:
    if credentials is None or not credentials.credentials:
        return None

    subject = decode_token(credentials.credentials, expected_type="access")
    if subject is None:
        return None

    try:
        user_id = uuid.UUID(subject)
    except ValueError:
        return None

    user = await user_crud.get_by_id(db, user_id)
    if user is None or not user.is_active:
        return None

    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    user = await _resolve_user(credentials, db)
    if user is None:
        raise CREDENTIALS_EXCEPTION
    return user


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Used by checkout so guests can order, but logged-in users get the order linked."""
    return await _resolve_user(credentials, db)
