"""Add optional classifications to attendance records without changing history."""

import os

from sqlalchemy import create_engine, text

from app.core import settings
from app.database import sqlalchemy_database_url


def main() -> None:
    statements = [
        "ALTER TABLE attendances ADD COLUMN IF NOT EXISTS activity VARCHAR(40)",
        "ALTER TABLE attendances ADD COLUMN IF NOT EXISTS opportunity VARCHAR(40)",
        "ALTER TABLE attendances ADD COLUMN IF NOT EXISTS non_opportunity VARCHAR(40)",
    ]
    database_url = os.getenv("DATABASE_URL_UNPOOLED") or settings().database_url
    engine = create_engine(sqlalchemy_database_url(database_url), pool_pre_ping=True)
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
    print("Attendance classification columns are ready.")


if __name__ == "__main__":
    main()
