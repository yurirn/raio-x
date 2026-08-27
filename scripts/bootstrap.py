"""Creates the physical schema and safe initial data for a new Raio X database."""

from sqlalchemy import select

from app.core import hash_password
from app.database import Base, SessionLocal, engine
from app.models import Coordinator, Reason, Regional, Role, Store, User


def get_or_create(session, model, defaults=None, **criteria):
    item = session.scalar(select(model).filter_by(**criteria))
    if item is None:
        item = model(**criteria, **(defaults or {}))
        session.add(item)
        session.flush()
    return item


def main():
    # Importing models above registers all tables on Base metadata before creation.
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        regional = get_or_create(session, Regional, name="SPL")
        coordinators = [
            get_or_create(session, Coordinator, regional_id=regional.id, name=name)
            for name in ("MARCUS", "MARISTELA", "HENRIQUE")
        ]
        get_or_create(session, Store, coordinator_id=coordinators[0].id, name="EXCEL")
        for name in (
            "Já Possui",
            "Sem Disponibilidade",
            "Não Aceitou",
            "Realta",
            "Dívida",
            "Fidelidade",
            "Cancelamento",
            "Configurar App",
            "Outros",
            "HABILITAÇÃO PRÉ/PÓS",
            "UPGRADE",
            "TOTALIZAÇÃO",
        ):
            get_or_create(session, Reason, name=name)
        admin = session.scalar(select(User).where(User.email == "admin@raiox.local"))
        if not admin:
            session.add(
                User(
                    name="Administrador",
                    email="admin@raiox.local",
                    password_hash=hash_password("TroqueEstaSenha123"),
                    role=Role.ADMIN,
                )
            )
        session.commit()
    print("Banco inicializado. Acesse com admin@raiox.local e troque a senha imediatamente.")


if __name__ == "__main__":
    main()
