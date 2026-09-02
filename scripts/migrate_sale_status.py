"""Add sale installation status and backfill existing sales."""

from sqlalchemy import text

from app.database import engine


def main() -> None:
    statements = [
        "ALTER TABLE attendances ADD COLUMN IF NOT EXISTS sale_status VARCHAR(40)",
        "CREATE INDEX IF NOT EXISTS ix_attendances_sale_status ON attendances (sale_status)",
        "UPDATE attendances SET sale_status = 'Aguardando Instalação' "
        "WHERE sale = 'YES' AND sale_status IS NULL",
    ]
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
    print("sale_status column is ready.")


if __name__ == "__main__":
    main()
