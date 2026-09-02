import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.database import get_session
from app.main import app
from app.schemas import AttendanceIn, LoginIn


def test_login_accepts_an_email_or_short_store_login():
    payload = LoginIn(email="admin@raiox.local", password="TroqueEstaSenha123")

    assert payload.email == "admin@raiox.local"
    assert LoginIn(email="Maua", password="maua@321").email == "maua"


def test_login_rejects_invalid_characters():
    with pytest.raises(ValidationError):
        LoginIn(email="admin\\@raiox.local", password="TroqueEstaSenha123")


def test_login_route_accepts_the_seeded_internal_email_format():
    class EmptySession:
        def scalar(self, _statement):
            return None

    app.dependency_overrides[get_session] = lambda: EmptySession()
    try:
        response = TestClient(app).post(
            "/api/auth/login",
            json={"email": "admin@raiox.local", "password": "TroqueEstaSenha123"},
        )
    finally:
        app.dependency_overrides.pop(get_session, None)

    assert response.status_code == 401


def test_attendance_requires_a_manually_informed_password_number():
    payload = {
        "date": "2026-08-26",
        "activity": "Físico",
        "cpf_cnpj": "01234567890",
        "ftth_available": "YES",
        "available_for_sale": "YES",
        "sale": "YES",
        "opportunity": "Disp Venda",
        "consultant_id": 1,
        "store_id": 1,
        "coordinator_id": 1,
        "regional_id": 1,
    }

    with pytest.raises(ValidationError):
        AttendanceIn(**payload)

    with pytest.raises(ValidationError):
        AttendanceIn(**payload, password_number=123)

    attendance = AttendanceIn(**payload, password_number=123, reason_id=1)

    assert attendance.password_number == 123


def test_attendance_requires_exactly_one_opportunity_classification():
    payload = {
        "date": "2026-08-26",
        "password_number": 123,
        "activity": "Mailing",
        "cpf_cnpj": "01234567890",
        "ftth_available": "YES",
        "available_for_sale": "YES",
        "sale": "NO",
        "reason_id": 1,
        "consultant_id": 1,
        "store_id": 1,
        "coordinator_id": 1,
        "regional_id": 1,
    }

    with pytest.raises(ValidationError):
        AttendanceIn(**payload)
    with pytest.raises(ValidationError):
        AttendanceIn(**payload, opportunity="Disp Venda", non_opportunity="Dívida")

    attendance = AttendanceIn(**payload, non_opportunity="Dívida")

    assert attendance.non_opportunity == "Dívida"
