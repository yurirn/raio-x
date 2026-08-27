"""Remove the legacy sale check and seed the three approved sale categories."""

from sqlalchemy import text

from app.database import SessionLocal, engine
from app.models import Reason
from scripts.bootstrap import get_or_create

SALE_REASONS = (
    "HABILITAÇÃO PRÉ/PÓS",
    "UPGRADE",
    "TOTALIZAÇÃO",
    "PRÉ PAGO",
    "OUTRAS OPERADORAS",
    "FIBRA AVULSA",
    "PJ",
)


def main():
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE attendances DROP CONSTRAINT IF EXISTS ck_reason_for_no_sale"))
        connection.execute(text("ALTER TABLE attendances DROP CONSTRAINT IF EXISTS ck_reason_required"))
    with SessionLocal() as session:
        for name in SALE_REASONS:
            get_or_create(session, Reason, name=name)
        session.commit()
    print("Motivos de venda atualizados.")


if __name__ == "__main__":
    main()
