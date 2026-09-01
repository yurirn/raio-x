"""Add the MANAGER role to an existing PostgreSQL database."""

from sqlalchemy import text

from app.database import engine


def main() -> None:
    if engine.dialect.name == "postgresql":
        with engine.begin() as connection:
            connection.execute(text("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'MANAGER'"))
    print("Papel MANAGER disponível.")


if __name__ == "__main__":
    main()
