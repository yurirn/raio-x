from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import decode_token
from app.database import get_session
from app.models import Role, Store, User, UserCoordinator, UserStore

bearer = HTTPBearer()


def current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    session: Session = Depends(get_session),
) -> User:
    payload = decode_token(credentials.credentials)
    user = session.get(User, int(payload["sub"]))
    if not user or not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário inativo ou inexistente"
        )
    return user


def require_roles(*roles: Role) -> Callable:
    def check(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão para esta ação"
            )
        return user

    return check


def allowed_store_ids(session: Session, user: User) -> list[int] | None:
    """None means unrestricted access; empty list means the user has no assigned stores."""
    if user.role == Role.ADMIN:
        return None
    if user.role == Role.COORDINATOR:
        coordinator_ids = select(UserCoordinator.coordinator_id).where(
            UserCoordinator.user_id == user.id
        )
        return list(
            session.scalars(select(Store.id).where(Store.coordinator_id.in_(coordinator_ids)))
        )
    return list(session.scalars(select(UserStore.store_id).where(UserStore.user_id == user.id)))


def assert_store_access(session: Session, user: User, store_id: int) -> None:
    allowed = allowed_store_ids(session, user)
    if allowed is not None and store_id not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Loja fora do escopo do usuário"
        )
