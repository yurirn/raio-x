"""Create or update a manager and attach it to named coordinators."""

import argparse

from sqlalchemy import select

from app.core import hash_password
from app.database import SessionLocal
from app.models import Coordinator, Role, User, UserCoordinator


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("login")
    parser.add_argument("name")
    parser.add_argument("coordinators", nargs="+")
    args = parser.parse_args()
    with SessionLocal() as session:
        manager = session.scalar(select(User).where(User.email == args.login))
        if manager is None:
            manager = User(name=args.name, email=args.login, password_hash=hash_password(f"{args.login}@321"), role=Role.MANAGER, active=True)
            session.add(manager)
            session.flush()
        elif manager.role != Role.MANAGER:
            raise ValueError(f"O login {args.login} já pertence a outro perfil.")
        coordinators = list(session.scalars(select(Coordinator).where(Coordinator.name.in_(args.coordinators))))
        found = {item.name for item in coordinators}
        missing = set(args.coordinators) - found
        if missing:
            raise ValueError(f"Coordenadores não encontrados: {', '.join(sorted(missing))}")
        session.query(UserCoordinator).filter(UserCoordinator.user_id == manager.id).delete()
        for coordinator in coordinators:
            session.add(UserCoordinator(user_id=manager.id, coordinator_id=coordinator.id))
        session.commit()
    print(f"Gerente {args.login} vinculado a {len(coordinators)} coordenadores.")


if __name__ == "__main__":
    main()
