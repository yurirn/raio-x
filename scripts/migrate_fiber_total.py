"""Add Fibra-Total flag to attendance records."""

from sqlalchemy import text

from app.database import engine


def main() -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE attendances "
                "ADD COLUMN IF NOT EXISTS has_fiber_total yes_no DEFAULT 'NO'"
            )
        )
    print("has_fiber_total column is ready.")


if __name__ == "__main__":
    main()
