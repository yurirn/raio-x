from fastapi.testclient import TestClient

from app.main import app


def test_local_frontend_on_port_3001_is_allowed():
    response = TestClient(app).options(
        "/api/auth/login",
        headers={
            "Origin": "http://localhost:3001",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3001"
