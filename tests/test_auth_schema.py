import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.database import get_session
from app.main import app
from app.schemas import AttendanceIn, LoginIn


def test_login_accepts_the_seeded_internal_email():
    payload = LoginIn(email="admin@raiox.local", password="TroqueEstaSenha123")

    assert payload.email == "admin@raiox.local"


def test_login_rejects_an_email_with_an_invalid_separator():
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
        "cpf_cnpj": "01234567890",
        "ftth_available": "YES",
        "available_for_sale": "YES",
        "sale": "YES",
        "consultant_id": 1,
        "store_id": 1,
        "coordinator_id": 1,
        "regional_id": 1,
    }

    with pytest.raises(ValidationError):
        AttendanceIn(**payload)

    attendance = AttendanceIn(**payload, password_number=123)

    assert attendance.password_number == 123
