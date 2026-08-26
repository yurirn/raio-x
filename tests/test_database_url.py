from app.database import sqlalchemy_database_url


def test_neon_postgres_url_uses_psycopg_driver():
    assert sqlalchemy_database_url("postgresql://user:pass@host/db") == (
        "postgresql+psycopg://user:pass@host/db"
    )


def test_existing_sqlalchemy_url_is_unchanged():
    url = "postgresql+psycopg://user:pass@host/db"
    assert sqlalchemy_database_url(url) == url
