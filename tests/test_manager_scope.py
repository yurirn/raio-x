from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import create_token, hash_password
from app.database import Base, get_session
from app.main import app
from app.models import Consultant, Coordinator, Regional, Role, Store, User, UserCoordinator


def test_manager_cannot_read_or_write_outside_assigned_coordinators():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    spl = Regional(name="SPL")
    spc = Regional(name="SPC")
    felipe_coordinator = Coordinator(name="Felipe scope", regional_id=1)
    sergio_coordinator = Coordinator(name="Sergio scope", regional_id=2)
    session.add_all([spl, spc])
    session.flush()
    felipe_coordinator.regional_id = spl.id
    sergio_coordinator.regional_id = spc.id
    session.add_all([felipe_coordinator, sergio_coordinator])
    session.flush()
    felipe_store = Store(name="Felipe loja", coordinator_id=felipe_coordinator.id)
    sergio_store = Store(name="Sergio loja", coordinator_id=sergio_coordinator.id)
    manager = User(name="Felipe", email="felipe", password_hash=hash_password("felipe@321"), role=Role.MANAGER)
    session.add_all([felipe_store, sergio_store, manager])
    session.flush()
    session.add(UserCoordinator(user_id=manager.id, coordinator_id=felipe_coordinator.id))
    session.add(Consultant(name="Consultor Sergio", store_id=sergio_store.id))
    session.commit()

    app.dependency_overrides[get_session] = lambda: session
    headers = {"Authorization": f"Bearer {create_token(manager.id, manager.role.value)}"}
    try:
        with TestClient(app) as client:
            visible = client.get("/api/catalog/stores", headers=headers)
            assert visible.status_code == 200
            assert [item["id"] for item in visible.json()] == [felipe_store.id]

            forbidden_store = client.post(
                "/api/admin/stores",
                headers=headers,
                json={"name": "Invasão", "coordinator_id": sergio_coordinator.id, "active": True},
            )
            assert forbidden_store.status_code == 403

            own_store = client.post(
                "/api/admin/stores",
                headers=headers,
                json={"name": "Nova loja Felipe", "coordinator_id": felipe_coordinator.id, "active": True},
            )
            assert own_store.status_code == 201

            forbidden_attendance = client.post(
                "/api/attendances",
                headers=headers,
                json={
                    "date": "2026-08-31",
                    "password_number": 1,
                    "activity": "Físico",
                    "cpf_cnpj": "01234567890",
                    "ftth_available": "YES",
                    "available_for_sale": "YES",
                    "sale": "NO",
                    "outcome_detail": "Não é decisor",
                    "non_opportunity": "Dívida",
                    "reason_id": 1,
                    "consultant_id": 1,
                    "store_id": sergio_store.id,
                    "coordinator_id": sergio_coordinator.id,
                    "regional_id": spc.id,
                },
            )
            assert forbidden_attendance.status_code == 403
    finally:
        app.dependency_overrides.pop(get_session, None)
        session.close()
