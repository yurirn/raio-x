"""Replace operator store accounts with short usernames and predictable initial passwords."""

from sqlalchemy import select

from app.core import hash_password
from app.database import SessionLocal
from app.models import Role, Store, User, UserStore
from scripts.import_spl import store_login


def main() -> None:
    with SessionLocal() as session:
        rows = session.execute(
            select(User, Store)
            .join(UserStore, UserStore.user_id == User.id)
            .join(Store, Store.id == UserStore.store_id)
            .where(User.role == Role.OPERATOR)
            .order_by(User.id)
        ).all()

        proposed = {user.id: store_login(store.name) for user, store in rows}
        if len(set(proposed.values())) != len(proposed):
            raise ValueError("Há lojas que geram o mesmo login abreviado.")

        existing = {
            user.email: user.id
            for user in session.scalars(select(User).where(User.email.in_(proposed.values())))
        }
        conflicts = [login for user_id, login in proposed.items() if existing.get(login, user_id) != user_id]
        if conflicts:
            raise ValueError(f"Os logins já pertencem a outros usuários: {', '.join(conflicts)}")

        for user, store in rows:
            login = proposed[user.id]
            user.email = login
            user.password_hash = hash_password(f"{login}@321")
            user.name = f"Loja {store.name}"

        session.commit()
    print(f"{len(rows)} logins de loja atualizados.")


if __name__ == "__main__":
    main()
