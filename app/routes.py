from datetime import date
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from openpyxl import Workbook
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.core import create_token, hash_password, verify_password
from app.database import get_session
from app.models import (
    Attendance,
    Consultant,
    Coordinator,
    Reason,
    Regional,
    Role,
    Store,
    User,
    UserCoordinator,
    UserStore,
    YesNo,
)
from app.schemas import (
    AttendanceIn,
    AttendanceOut,
    AttendancePatch,
    ConsultantIn,
    CoordinatorIn,
    LoginIn,
    ReasonIn,
    RegionalIn,
    StoreIn,
    TokenOut,
    UserIn,
    UserPatch,
)
from app.security import allowed_store_ids, assert_store_access, current_user, require_roles
from app.services import (
    add_audit,
    aggregate_metrics,
    attendance_snapshot,
    validate_hierarchy,
    validate_reason,
)

router = APIRouter(prefix="/api")


@router.post("/auth/login", response_model=TokenOut)
def login(payload: LoginIn, session: Session = Depends(get_session)):
    user = session.scalar(select(User).where(User.email == payload.email))
    if not user or not user.active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Login ou senha inválidos"
        )
    return TokenOut(access_token=create_token(user.id, user.role.value))


@router.get("/me")
def me(session: Session = Depends(get_session), user: User = Depends(current_user)):
    store_context = None
    store_ids = allowed_store_ids(session, user)
    if user.role == Role.OPERATOR and store_ids and len(store_ids) == 1:
        store = session.get(Store, store_ids[0])
        coordinator = session.get(Coordinator, store.coordinator_id) if store else None
        regional = session.get(Regional, coordinator.regional_id) if coordinator else None
        if store and coordinator and regional:
            store_context = {
                "regional_id": regional.id,
                "regional_name": regional.name,
                "coordinator_id": coordinator.id,
                "coordinator_name": coordinator.name,
                "store_id": store.id,
                "store_name": store.name,
            }
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "can_edit_password_number": user.can_edit_password_number,
        "store_context": store_context,
    }


def list_active(model, parent_column=None, parent_id=None, session: Session = None):
    query = select(model).where(model.active.is_(True)).order_by(model.name)
    if parent_column is not None and parent_id is not None:
        query = query.where(parent_column == parent_id)
    return session.scalars(query).all()


@router.get("/catalog/regionals")
def catalog_regionals(session: Session = Depends(get_session), user: User = Depends(current_user)):
    allowed = allowed_store_ids(session, user)
    query = select(Regional).where(Regional.active.is_(True)).order_by(Regional.name)
    if allowed is not None:
        query = (
            query.join(Coordinator, Coordinator.regional_id == Regional.id)
            .join(Store, Store.coordinator_id == Coordinator.id)
            .where(Store.id.in_(allowed))
            .distinct()
        )
    return session.scalars(query).all()


@router.get("/catalog/coordinators")
def catalog_coordinators(
    regional_id: int | None = None,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
):
    allowed = allowed_store_ids(session, user)
    query = select(Coordinator).where(Coordinator.active.is_(True)).order_by(Coordinator.name)
    if regional_id:
        query = query.where(Coordinator.regional_id == regional_id)
    if allowed is not None:
        query = query.join(Store).where(Store.id.in_(allowed)).distinct()
    return session.scalars(query).all()


@router.get("/catalog/stores")
def catalog_stores(
    coordinator_id: int | None = None,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
):
    query = select(Store).where(Store.active.is_(True)).order_by(Store.name)
    if coordinator_id:
        query = query.where(Store.coordinator_id == coordinator_id)
    allowed = allowed_store_ids(session, user)
    if allowed is not None:
        query = query.where(Store.id.in_(allowed))
    return session.scalars(query).all()


@router.get("/catalog/consultants")
def catalog_consultants(
    store_id: int, session: Session = Depends(get_session), user: User = Depends(current_user)
):
    assert_store_access(session, user, store_id)
    return list_active(Consultant, Consultant.store_id, store_id, session)


@router.get("/catalog/reasons")
def catalog_reasons(session: Session = Depends(get_session), user: User = Depends(current_user)):
    return list_active(Reason, session=session)


def scoped_attendances(query: Select, session: Session, user: User) -> Select:
    allowed = allowed_store_ids(session, user)
    return query if allowed is None else query.where(Attendance.store_id.in_(allowed))


@router.post("/attendances", response_model=AttendanceOut, status_code=status.HTTP_201_CREATED)
def create_attendance(
    payload: AttendanceIn,
    session: Session = Depends(get_session),
    user: User = Depends(require_roles(Role.ADMIN, Role.OPERATOR)),
):
    assert_store_access(session, user, payload.store_id)
    validate_hierarchy(
        session,
        payload.regional_id,
        payload.coordinator_id,
        payload.store_id,
        payload.consultant_id,
    )
    validate_reason(session, payload.sale, payload.reason_id)
    attendance = Attendance(
        **payload.model_dump(exclude={"password_number"}),
        password_number=payload.password_number,
        created_by=user.id,
        updated_by=user.id,
    )
    session.add(attendance)
    try:
        session.flush()
    except Exception as exc:
        session.rollback()
        raise HTTPException(
            status_code=409, detail="Senha já existe para esta loja e data"
        ) from exc
    add_audit(
        session,
        "attendance",
        attendance.id,
        "CREATE",
        user.id,
        after=attendance_snapshot(attendance),
    )
    session.commit()
    session.refresh(attendance)
    return attendance


@router.get("/attendances")
def list_attendances(
    start_date: date | None = None,
    end_date: date | None = None,
    regional_id: int | None = None,
    coordinator_id: int | None = None,
    store_id: int | None = None,
    consultant_id: int | None = None,
    sale: YesNo | None = None,
    ftth_available: YesNo | None = None,
    reason_id: int | None = None,
    cpf_cnpj: str | None = None,
    password_number: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
):
    query = scoped_attendances(select(Attendance), session, user)
    fields = [
        (Attendance.date >= start_date, start_date),
        (Attendance.date <= end_date, end_date),
        (Attendance.regional_id == regional_id, regional_id),
        (Attendance.coordinator_id == coordinator_id, coordinator_id),
        (Attendance.store_id == store_id, store_id),
        (Attendance.consultant_id == consultant_id, consultant_id),
        (Attendance.sale == sale, sale),
        (Attendance.ftth_available == ftth_available, ftth_available),
        (Attendance.reason_id == reason_id, reason_id),
        (Attendance.password_number == password_number, password_number),
    ]
    query = query.where(*[condition for condition, value in fields if value is not None])
    if cpf_cnpj:
        query = query.where(Attendance.cpf_cnpj.ilike(f"%{cpf_cnpj.strip()}%"))
    total = len(session.scalars(query).all())
    items = session.scalars(
        query.order_by(Attendance.date.desc(), Attendance.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return {"items": items, "page": page, "page_size": page_size, "total": total}


@router.patch("/attendances/{attendance_id}", response_model=AttendanceOut)
def update_attendance(
    attendance_id: int,
    payload: AttendancePatch,
    session: Session = Depends(get_session),
    user: User = Depends(require_roles(Role.ADMIN, Role.OPERATOR)),
):
    attendance = session.get(Attendance, attendance_id)
    if not attendance:
        raise HTTPException(status_code=404, detail="Atendimento não encontrado")
    assert_store_access(session, user, attendance.store_id)
    changes = payload.model_dump(exclude_unset=True)
    before = attendance_snapshot(attendance)
    for key, value in changes.items():
        setattr(attendance, key, value)
    validate_reason(session, attendance.sale, attendance.reason_id)
    consultant = session.get(Consultant, attendance.consultant_id)
    if not consultant or consultant.store_id != attendance.store_id:
        raise HTTPException(
            status_code=422, detail="Consultor deve pertencer à loja do atendimento"
        )
    attendance.updated_by = user.id
    add_audit(
        session,
        "attendance",
        attendance.id,
        "UPDATE",
        user.id,
        before,
        attendance_snapshot(attendance),
    )
    session.commit()
    session.refresh(attendance)
    return attendance


@router.delete("/attendances/{attendance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attendance(
    attendance_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(require_roles(Role.ADMIN, Role.OPERATOR)),
):
    attendance = session.get(Attendance, attendance_id)
    if not attendance:
        raise HTTPException(status_code=404, detail="Atendimento não encontrado")
    assert_store_access(session, user, attendance.store_id)
    add_audit(
        session,
        "attendance",
        attendance.id,
        "DELETE",
        user.id,
        before=attendance_snapshot(attendance),
    )
    session.delete(attendance)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def dashboard_rows(
    session: Session,
    user: User,
    start_date: date,
    end_date: date,
    regional_id: int | None,
    coordinator_id: int | None,
    store_id: int | None,
    consultant_id: int | None,
):
    query = scoped_attendances(
        select(
            Attendance.consultant_id,
            Consultant.name,
            Attendance.date,
            Attendance.ftth_available,
            Attendance.available_for_sale,
            Attendance.sale,
        ).join(Consultant),
        session,
        user,
    ).where(Attendance.date.between(start_date, end_date))
    filters = [
        (Attendance.regional_id, regional_id),
        (Attendance.coordinator_id, coordinator_id),
        (Attendance.store_id, store_id),
        (Attendance.consultant_id, consultant_id),
    ]
    return session.execute(
        query.where(*[field == value for field, value in filters if value is not None])
    ).all()


@router.get("/dashboard/consolidated")
def consolidated(
    start_date: date,
    end_date: date,
    regional_id: int | None = None,
    coordinator_id: int | None = None,
    store_id: int | None = None,
    consultant_id: int | None = None,
    ranking_by: str = Query("sales", pattern="^(sales|conversion|passwords|availability)$"),
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
):
    if end_date < start_date:
        raise HTTPException(
            status_code=422, detail="A data final deve ser igual ou posterior à inicial"
        )
    data = aggregate_metrics(
        dashboard_rows(
            session,
            user,
            start_date,
            end_date,
            regional_id,
            coordinator_id,
            store_id,
            consultant_id,
        )
    )
    metric = {
        "sales": "sales",
        "conversion": "conversion",
        "passwords": "passwords",
        "availability": "availability_percentage",
    }[ranking_by]
    ranking = sorted(
        data["performance"], key=lambda item: (-item[metric], item["consultant"].lower())
    )
    for position, item in enumerate(ranking, 1):
        item["position"] = position
    reasons_query = scoped_attendances(
        select(Reason.name, func.count(Attendance.id))
        .join(Reason)
        .where(Attendance.date.between(start_date, end_date), Attendance.sale == YesNo.NO),
        session,
        user,
    )
    for field, value in [
        (Attendance.regional_id, regional_id),
        (Attendance.coordinator_id, coordinator_id),
        (Attendance.store_id, store_id),
        (Attendance.consultant_id, consultant_id),
    ]:
        if value is not None:
            reasons_query = reasons_query.where(field == value)
    data["ranking"] = ranking
    data["reasons"] = [
        {"reason": name, "count": count}
        for name, count in session.execute(
            reasons_query.group_by(Reason.name).order_by(func.count().desc())
        )
    ]
    data["filters"] = {
        "start_date": start_date,
        "end_date": end_date,
        "regional_id": regional_id,
        "coordinator_id": coordinator_id,
        "store_id": store_id,
        "consultant_id": consultant_id,
    }
    return data


@router.get("/dashboard/consultants/{consultant_id}")
def consultant_detail(
    consultant_id: int,
    start_date: date,
    end_date: date,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
):
    consultant = session.get(Consultant, consultant_id)
    if not consultant:
        raise HTTPException(status_code=404, detail="Consultor não encontrado")
    assert_store_access(session, user, consultant.store_id)
    metrics = aggregate_metrics(
        dashboard_rows(session, user, start_date, end_date, None, None, None, consultant_id)
    )
    rows = session.scalars(
        scoped_attendances(select(Attendance), session, user)
        .where(
            Attendance.consultant_id == consultant_id, Attendance.date.between(start_date, end_date)
        )
        .order_by(Attendance.date.desc(), Attendance.password_number.desc())
    ).all()
    reasons = session.execute(
        scoped_attendances(
            select(Reason.name, func.count(Attendance.id)).join(Reason), session, user
        )
        .where(
            Attendance.consultant_id == consultant_id,
            Attendance.date.between(start_date, end_date),
            Attendance.sale == YesNo.NO,
        )
        .group_by(Reason.name)
    ).all()
    return {
        "consultant": {"id": consultant.id, "name": consultant.name},
        "metrics": metrics["cards"],
        "top_reasons": [{"reason": name, "count": count} for name, count in reasons],
        "attendances": rows,
    }


@router.get("/exports/attendances.xlsx")
def export_attendances(
    start_date: date,
    end_date: date,
    store_id: int | None = None,
    consultant_id: int | None = None,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
):
    query = scoped_attendances(
        select(Attendance).where(Attendance.date.between(start_date, end_date)), session, user
    )
    if store_id:
        query = query.where(Attendance.store_id == store_id)
    if consultant_id:
        query = query.where(Attendance.consultant_id == consultant_id)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Atendimentos"
    sheet.append(
        [
            "Data",
            "Senha",
            "CPF/CNPJ",
            "Plano",
            "FTTH",
            "Disponível para venda",
            "Venda",
            "Motivo",
            "Consultor",
        ]
    )
    reasons = {item.id: item.name for item in session.scalars(select(Reason)).all()}
    consultants = {item.id: item.name for item in session.scalars(select(Consultant)).all()}
    for item in session.scalars(query.order_by(Attendance.date, Attendance.password_number)):
        sheet.append(
            [
                item.date.isoformat(),
                item.password_number,
                item.cpf_cnpj,
                item.current_plan,
                item.ftth_available.value,
                item.available_for_sale.value,
                item.sale.value,
                reasons.get(item.reason_id, ""),
                consultants.get(item.consultant_id, ""),
            ]
        )
    stream = BytesIO()
    workbook.save(stream)
    return Response(
        stream.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=atendimentos.xlsx"},
    )


@router.get("/exports/consolidated.xlsx")
def export_consolidated(
    start_date: date,
    end_date: date,
    regional_id: int | None = None,
    coordinator_id: int | None = None,
    store_id: int | None = None,
    consultant_id: int | None = None,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
):
    metrics = aggregate_metrics(
        dashboard_rows(
            session,
            user,
            start_date,
            end_date,
            regional_id,
            coordinator_id,
            store_id,
            consultant_id,
        )
    )
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Consolidado"
    sheet.append(
        [
            "Consultor",
            "Senhas",
            "Possui Disponibilidade",
            "Disponível para Venda",
            "Vendas",
            "Participação nas Senhas (%)",
            "% Disponibilidade",
            "% Disponibilidade Real",
            "Conversão (%)",
        ]
    )
    for row in metrics["performance"]:
        sheet.append(
            [
                row["consultant"],
                row["passwords"],
                row["ftth_available"],
                row["available_for_sale"],
                row["sales"],
                row["share_passwords"],
                row["availability_percentage"],
                row["availability_real_percentage"],
                row["conversion"],
            ]
        )
    stream = BytesIO()
    workbook.save(stream)
    return Response(
        stream.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=consolidado.xlsx"},
    )


ADMIN = Depends(require_roles(Role.ADMIN))


def user_public(item: User) -> dict:
    return {
        "id": item.id,
        "name": item.name,
        "email": item.email,
        "role": item.role,
        "active": item.active,
        "can_edit_password_number": item.can_edit_password_number,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


def admin_crud(path: str, model, payload_type):
    @router.get(path, dependencies=[ADMIN])
    def list_items(include_inactive: bool = False, session: Session = Depends(get_session)):
        query = select(model).order_by(model.name)
        if not include_inactive:
            query = query.where(model.active.is_(True))
        return session.scalars(query).all()

    @router.post(path, status_code=201, dependencies=[ADMIN])
    def create_item(
        payload: payload_type,
        session: Session = Depends(get_session),
        user: User = Depends(current_user),
    ):
        item = model(**payload.model_dump())
        session.add(item)
        session.flush()
        add_audit(
            session, model.__tablename__, item.id, "CREATE", user.id, after={"name": item.name}
        )
        session.commit()
        session.refresh(item)
        return item

    @router.patch(f"{path}/{{item_id}}", dependencies=[ADMIN])
    def update_item(
        item_id: int,
        payload: payload_type,
        session: Session = Depends(get_session),
        user: User = Depends(current_user),
    ):
        item = session.get(model, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Cadastro não encontrado")
        before = {"name": item.name, "active": item.active}
        for key, value in payload.model_dump().items():
            setattr(item, key, value)
        add_audit(
            session,
            model.__tablename__,
            item.id,
            "UPDATE",
            user.id,
            before,
            {"name": item.name, "active": item.active},
        )
        session.commit()
        session.refresh(item)
        return item


admin_crud("/admin/regionals", Regional, RegionalIn)
admin_crud("/admin/coordinators", Coordinator, CoordinatorIn)
admin_crud("/admin/stores", Store, StoreIn)
admin_crud("/admin/consultants", Consultant, ConsultantIn)
admin_crud("/admin/reasons", Reason, ReasonIn)


@router.get("/admin/users", dependencies=[ADMIN])
def admin_users(session: Session = Depends(get_session)):
    return [user_public(item) for item in session.scalars(select(User).order_by(User.name))]


def apply_user_scopes(
    session: Session, user: User, coordinator_ids: list[int], store_ids: list[int]
) -> None:
    session.query(UserCoordinator).filter(UserCoordinator.user_id == user.id).delete()
    session.query(UserStore).filter(UserStore.user_id == user.id).delete()
    for coordinator_id in coordinator_ids:
        session.add(UserCoordinator(user_id=user.id, coordinator_id=coordinator_id))
    for store_id in store_ids:
        session.add(UserStore(user_id=user.id, store_id=store_id))


@router.post("/admin/users", status_code=201, dependencies=[ADMIN])
def create_user(
    payload: UserIn, session: Session = Depends(get_session), user: User = Depends(current_user)
):
    if session.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(status_code=409, detail="E-mail já cadastrado")
    item = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        active=payload.active,
        can_edit_password_number=payload.can_edit_password_number,
    )
    session.add(item)
    session.flush()
    apply_user_scopes(session, item, payload.coordinator_ids, payload.store_ids)
    add_audit(
        session,
        "users",
        item.id,
        "CREATE",
        user.id,
        after={"name": item.name, "role": item.role.value},
    )
    session.commit()
    session.refresh(item)
    return user_public(item)


@router.patch("/admin/users/{user_id}", dependencies=[ADMIN])
def update_user(
    user_id: int,
    payload: UserPatch,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
):
    item = session.get(User, user_id)
    if not item:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    changes = payload.model_dump(exclude_unset=True)
    coordinator_ids = changes.pop("coordinator_ids", None)
    store_ids = changes.pop("store_ids", None)
    if "password" in changes:
        changes["password_hash"] = hash_password(changes.pop("password"))
    for key, value in changes.items():
        setattr(item, key, value)
    if coordinator_ids is not None or store_ids is not None:
        apply_user_scopes(session, item, coordinator_ids or [], store_ids or [])
    add_audit(
        session,
        "users",
        item.id,
        "UPDATE",
        user.id,
        after={"name": item.name, "role": item.role.value},
    )
    session.commit()
    session.refresh(item)
    return user_public(item)
