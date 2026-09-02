from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Role(StrEnum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    COORDINATOR = "COORDINATOR"
    OPERATOR = "OPERATOR"


class YesNo(StrEnum):
    YES = "YES"
    NO = "NO"


class Timestamped:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Regional(Timestamped, Base):
    __tablename__ = "regionals"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Coordinator(Timestamped, Base):
    __tablename__ = "coordinators"
    id: Mapped[int] = mapped_column(primary_key=True)
    regional_id: Mapped[int] = mapped_column(ForeignKey("regionals.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (UniqueConstraint("regional_id", "name"),)


class Store(Timestamped, Base):
    __tablename__ = "stores"
    id: Mapped[int] = mapped_column(primary_key=True)
    coordinator_id: Mapped[int] = mapped_column(ForeignKey("coordinators.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (UniqueConstraint("coordinator_id", "name"),)


class Consultant(Timestamped, Base):
    __tablename__ = "consultants"
    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (UniqueConstraint("store_id", "name"),)


class Reason(Timestamped, Base):
    __tablename__ = "reasons"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class User(Timestamped, Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role, name="user_role"), index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    can_edit_password_number: Mapped[bool] = mapped_column(Boolean, default=False)


class UserCoordinator(Base):
    __tablename__ = "user_coordinators"
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    coordinator_id: Mapped[int] = mapped_column(
        ForeignKey("coordinators.id", ondelete="CASCADE"), primary_key=True
    )


class UserStore(Base):
    __tablename__ = "user_stores"
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id", ondelete="CASCADE"), primary_key=True
    )


class Attendance(Timestamped, Base):
    __tablename__ = "attendances"
    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    password_number: Mapped[int] = mapped_column(Integer)
    activity: Mapped[str | None] = mapped_column(String(40))
    cpf_cnpj: Mapped[str] = mapped_column(String(18), index=True)
    current_plan: Mapped[str | None] = mapped_column(String(255))
    opportunity: Mapped[str | None] = mapped_column(String(40))
    non_opportunity: Mapped[str | None] = mapped_column(String(40))
    has_fiber_total: Mapped[YesNo] = mapped_column(
        Enum(YesNo, name="yes_no"), default=YesNo.NO, server_default="NO"
    )
    ftth_available: Mapped[YesNo] = mapped_column(Enum(YesNo, name="yes_no"), index=True)
    available_for_sale: Mapped[YesNo] = mapped_column(Enum(YesNo, name="yes_no"), index=True)
    sale: Mapped[YesNo] = mapped_column(Enum(YesNo, name="yes_no"), index=True)
    sale_status: Mapped[str | None] = mapped_column(String(40), index=True)
    order_number: Mapped[str | None] = mapped_column(String(30))
    outcome_detail: Mapped[str | None] = mapped_column(String(80))
    reason_id: Mapped[int | None] = mapped_column(ForeignKey("reasons.id"), index=True)
    consultant_id: Mapped[int] = mapped_column(ForeignKey("consultants.id"), index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), index=True)
    coordinator_id: Mapped[int] = mapped_column(ForeignKey("coordinators.id"), index=True)
    regional_id: Mapped[int] = mapped_column(ForeignKey("regionals.id"), index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    __table_args__ = (
        UniqueConstraint(
            "store_id", "date", "password_number", name="uq_attendance_store_day_password"
        ),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    entity: Mapped[str] = mapped_column(String(60), index=True)
    entity_id: Mapped[int] = mapped_column(Integer, index=True)
    action: Mapped[str] = mapped_column(String(20))
    before: Mapped[dict | None] = mapped_column(JSON)
    after: Mapped[dict | None] = mapped_column(JSON)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
