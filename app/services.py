from collections import defaultdict
from datetime import date

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Attendance,
    AuditLog,
    Consultant,
    Coordinator,
    Reason,
    Regional,
    Store,
    YesNo,
)

DEFAULT_SALE_STATUS = "Aguardando Instalação"
SALE_STATUSES = (
    DEFAULT_SALE_STATUS,
    "Instalada",
    "Cancelada",
    "Reagendada",
    "Pendência",
)


def sale_status_for(sale: YesNo, current: str | None = None) -> str | None:
    if sale != YesNo.YES:
        return None
    if current in SALE_STATUSES:
        return current
    return DEFAULT_SALE_STATUS


SALE_REASON_NAMES = {
    "HABILITAÇÃO PRÉ/PÓS",
    "UPGRADE",
    "TOTALIZAÇÃO",
    "PRÉ PAGO",
    "OUTRAS OPERADORAS",
    "FIBRA AVULSA",
    "PJ",
}


def attendance_snapshot(item: Attendance) -> dict:
    return {
        key: (value.value if isinstance(value, YesNo) else value)
        for key, value in {
            "date": item.date.isoformat(),
            "password_number": item.password_number,
            "activity": item.activity,
            "cpf_cnpj": item.cpf_cnpj,
            "current_plan": item.current_plan,
            "opportunity": item.opportunity,
            "non_opportunity": item.non_opportunity,
            "has_fiber_total": item.has_fiber_total,
            "ftth_available": item.ftth_available,
            "available_for_sale": item.available_for_sale,
            "sale": item.sale,
            "sale_status": item.sale_status,
            "order_number": item.order_number,
            "outcome_detail": item.outcome_detail,
            "reason_id": item.reason_id,
            "consultant_id": item.consultant_id,
            "store_id": item.store_id,
            "coordinator_id": item.coordinator_id,
            "regional_id": item.regional_id,
        }.items()
    }


def add_audit(
    session: Session,
    entity: str,
    entity_id: int,
    action: str,
    user_id: int,
    before: dict | None = None,
    after: dict | None = None,
) -> None:
    session.add(
        AuditLog(
            entity=entity,
            entity_id=entity_id,
            action=action,
            user_id=user_id,
            before=before,
            after=after,
        )
    )


def validate_hierarchy(
    session: Session, regional_id: int, coordinator_id: int, store_id: int, consultant_id: int
) -> None:
    regional = session.get(Regional, regional_id)
    coordinator = session.get(Coordinator, coordinator_id)
    store = session.get(Store, store_id)
    consultant = session.get(Consultant, consultant_id)
    if not all([regional, coordinator, store, consultant]):
        raise HTTPException(
            status_code=422, detail="Regional, coordenador, loja ou consultor inválido"
        )
    if not all([regional.active, coordinator.active, store.active, consultant.active]):
        raise HTTPException(
            status_code=422, detail="Não é permitido lançar para um cadastro inativo"
        )
    if (
        coordinator.regional_id != regional_id
        or store.coordinator_id != coordinator_id
        or consultant.store_id != store_id
    ):
        raise HTTPException(
            status_code=422,
            detail="A hierarquia Regional > Coordenador > Loja > Consultor é inválida",
        )


def validate_reason(session: Session, sale: YesNo, reason_id: int | None) -> None:
    if not reason_id:
        raise HTTPException(status_code=422, detail="Motivo é obrigatório para o atendimento")
    reason = session.get(Reason, reason_id)
    if not reason or not reason.active:
        raise HTTPException(status_code=422, detail="Motivo inválido ou inativo")
    if sale == YesNo.YES and reason.name not in SALE_REASON_NAMES:
        raise HTTPException(status_code=422, detail="Selecione um motivo de venda válido")
    if sale == YesNo.NO and reason.name in SALE_REASON_NAMES:
        raise HTTPException(status_code=422, detail="Selecione um motivo de não venda válido")


def unused_password_numbers(used: list[int]) -> list[int]:
    if not used:
        return []
    taken = set(used)
    return [number for number in range(1, max(taken)) if number not in taken]


def unused_passwords(session: Session, store_id: int, day: date) -> list[int]:
    used = list(
        session.scalars(
            select(Attendance.password_number).where(
                Attendance.store_id == store_id, Attendance.date == day
            )
        )
    )
    return unused_password_numbers(used)


def next_password(session: Session, store_id: int, day: date) -> int:
    value = session.scalar(
        select(func.coalesce(func.max(Attendance.password_number), 0)).where(
            Attendance.store_id == store_id, Attendance.date == day
        )
    )
    return int(value) + 1


def percentage(numerator: int, denominator: int) -> float:
    return round((numerator / denominator * 100) if denominator else 0, 2)


def availability_real(total: int, available_for_sale: int) -> float:
    """Centralized business rule. Initial rule: eligible-for-sale / total attendances."""
    return percentage(available_for_sale, total)


def aggregate_metrics(rows: list[tuple]) -> dict:
    """Rows contain consultant/store ids and names, date, FTTH, availability and sale."""
    people: dict[int, dict] = {}
    stores: dict[int, dict] = {}
    daily: dict[str, dict] = defaultdict(lambda: {"passwords": 0, "sales": 0, "available": 0})
    for consultant_id, name, store_id, store_name, day, ftth, available, sale in rows:
        item = people.setdefault(
            consultant_id,
            {
                "consultant_id": consultant_id,
                "consultant": name,
                "passwords": 0,
                "ftth_available": 0,
                "available_for_sale": 0,
                "sales": 0,
            },
        )
        item["passwords"] += 1
        item["ftth_available"] += ftth == YesNo.YES
        item["available_for_sale"] += available == YesNo.YES
        item["sales"] += sale == YesNo.YES
        store = stores.setdefault(
            store_id,
            {
                "store_id": store_id,
                "store": store_name,
                "passwords": 0,
                "ftth_available": 0,
                "available_for_sale": 0,
                "sales": 0,
            },
        )
        store["passwords"] += 1
        store["ftth_available"] += ftth == YesNo.YES
        store["available_for_sale"] += available == YesNo.YES
        store["sales"] += sale == YesNo.YES
        bucket = daily[day.isoformat()]
        bucket["passwords"] += 1
        bucket["sales"] += sale == YesNo.YES
        bucket["available"] += available == YesNo.YES
    total = {
        "passwords": sum(x["passwords"] for x in people.values()),
        "ftth_available": sum(x["ftth_available"] for x in people.values()),
        "available_for_sale": sum(x["available_for_sale"] for x in people.values()),
        "sales": sum(x["sales"] for x in people.values()),
    }
    def with_percentages(items: dict[int, dict], label: str) -> list[dict]:
        performance = []
        for item in items.values():
            item |= {
                "share_passwords": percentage(item["passwords"], total["passwords"]),
                "availability_percentage": percentage(
                    item["available_for_sale"], item["ftth_available"]
                ),
                "availability_real_percentage": availability_real(
                    item["passwords"], item["available_for_sale"]
                ),
                "conversion": percentage(item["sales"], item["available_for_sale"]),
            }
            performance.append(item)
        performance.sort(key=lambda item: (-item["sales"], item[label].lower()))
        for position, item in enumerate(performance, 1):
            item["position"] = position
        return performance

    performance = with_percentages(people, "consultant")
    store_performance = with_percentages(stores, "store")
    charts = [
        {"date": day, **values, "conversion": percentage(values["sales"], values["available"])}
        for day, values in sorted(daily.items())
    ]
    return {
        "cards": {
            **total,
            "conversion": percentage(total["sales"], total["available_for_sale"]),
            "active_consultants": len(people),
        },
        "performance": performance,
        "store_performance": store_performance,
        "daily": charts,
    }
