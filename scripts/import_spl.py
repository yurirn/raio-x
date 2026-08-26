"""Import the SPL store hierarchy, consultants, and one operator account per store."""

import argparse
import re
import unicodedata
from pathlib import Path

from openpyxl import load_workbook
from sqlalchemy import select

from app.core import hash_password
from app.database import SessionLocal
from app.models import Consultant, Coordinator, Regional, Role, Store, User, UserStore


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", normalized.lower())).strip("-")


def store_login(store_name: str) -> str:
    """Create the short username used by a store, e.g. ``maua``."""
    without_code = re.sub(r"^\s*\d+\s*-\s*", "", store_name)
    without_suffix = re.sub(r"\s*-\s*comm\s*$", "", without_code, flags=re.IGNORECASE)
    login = slugify(without_suffix).replace("-", "")
    if not login:
        raise ValueError(f"Não foi possível gerar um login para a loja: {store_name}")
    return login


def get_or_create(session, model, **criteria):
    item = session.scalar(select(model).filter_by(**criteria))
    if item is None:
        item = model(**criteria)
        session.add(item)
        session.flush()
    return item


def rows_from_workbook(path: Path) -> list[tuple[str, str, str]]:
    sheet = load_workbook(path, read_only=True, data_only=True).active
    rows = []
    for row_number, values in enumerate(sheet.iter_rows(values_only=True), start=1):
        consultant, store, coordinator = (str(value or "").strip() for value in values[:3])
        if not all((consultant, store, coordinator)):
            raise ValueError(f"Linha {row_number} precisa ter consultor, loja e coordenador.")
        rows.append((consultant, store, coordinator))
    if not rows:
        raise ValueError("A planilha não possui linhas para importar.")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workbook", type=Path)
    args = parser.parse_args()

    rows = rows_from_workbook(args.workbook)
    with SessionLocal() as session:
        regional = get_or_create(session, Regional, name="SPL")
        coordinator_by_name: dict[str, Coordinator] = {}
        store_by_key: dict[tuple[str, str], Store] = {}
        imported_consultants = 0

        for consultant_name, store_name, coordinator_name in rows:
            coordinator = coordinator_by_name.get(coordinator_name)
            if coordinator is None:
                coordinator = get_or_create(
                    session, Coordinator, regional_id=regional.id, name=coordinator_name
                )
                coordinator_by_name[coordinator_name] = coordinator
            store_key = (coordinator_name, store_name)
            store = store_by_key.get(store_key)
            if store is None:
                store = get_or_create(
                    session, Store, coordinator_id=coordinator.id, name=store_name
                )
                store_by_key[store_key] = store
            get_or_create(session, Consultant, store_id=store.id, name=consultant_name)
            imported_consultants += 1

        created_users = 0
        store_logins: set[str] = set()
        for (_, store_name), store in store_by_key.items():
            login = store_login(store_name)
            if login in store_logins:
                raise ValueError(f"Login duplicado gerado para a loja: {store_name}")
            store_logins.add(login)
            user = session.scalar(select(User).where(User.email == login))
            if user is None:
                user = User(
                    name=f"Loja {store_name}",
                    email=login,
                    password_hash=hash_password(f"{login}@321"),
                    role=Role.OPERATOR,
                    active=True,
                )
                session.add(user)
                session.flush()
                created_users += 1
            session.query(UserStore).filter(UserStore.user_id == user.id).delete()
            session.add(UserStore(user_id=user.id, store_id=store.id))

        session.commit()
        print(
            f"Importação concluída: {imported_consultants} consultores, "
            f"{len(store_by_key)} lojas, {len(coordinator_by_name)} coordenadores e "
            f"{created_users} novos logins de loja."
        )


if __name__ == "__main__":
    main()
