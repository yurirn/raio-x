"""Add optional finalization fields to attendance records without changing history."""

from sqlalchemy import text

from app.database import engine


def main() -> None:
    statements = [
        "ALTER TABLE attendances ADD COLUMN IF NOT EXISTS order_number VARCHAR(30)",
        "ALTER TABLE attendances ADD COLUMN IF NOT EXISTS outcome_detail VARCHAR(80)",
    ]
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
    print("Attendance finalization columns are ready.")


if __name__ == "__main__":
    main()
