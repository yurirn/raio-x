import re
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models import Role, YesNo

LOGIN_PATTERN = re.compile(r"^[a-z0-9._@-]+$")


def normalize_login(value: str) -> str:
    normalized = value.strip().lower()
    if not LOGIN_PATTERN.fullmatch(normalized):
        raise ValueError("Informe um login válido, sem espaços ou caracteres especiais")
    return normalized


normalize_email = normalize_login


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginIn(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return normalize_login(value)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class NamedIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    active: bool = True


class RegionalIn(NamedIn):
    pass


class CoordinatorIn(NamedIn):
    regional_id: int


class StoreIn(NamedIn):
    coordinator_id: int


class ConsultantIn(NamedIn):
    store_id: int


class ReasonIn(NamedIn):
    pass


class UserIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str
    password: str = Field(min_length=8, max_length=128)
    role: Role
    active: bool = True
    can_edit_password_number: bool = False
    coordinator_ids: list[int] = []
    store_ids: list[int] = []

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return normalize_email(value)


class UserPatch(BaseModel):
    name: str | None = None
    email: str | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
    role: Role | None = None
    active: bool | None = None
    can_edit_password_number: bool | None = None
    coordinator_ids: list[int] | None = None
    store_ids: list[int] | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        return normalize_email(value) if value is not None else None


class AttendanceIn(BaseModel):
    date: date
    password_number: int = Field(ge=1)
    activity: str = Field(min_length=1, max_length=40)
    cpf_cnpj: str = Field(min_length=1, max_length=18)
    current_plan: str | None = Field(default=None, max_length=255)
    opportunity: str | None = Field(default=None, max_length=40)
    non_opportunity: str | None = Field(default=None, max_length=40)
    has_fiber_total: YesNo
    ftth_available: YesNo
    available_for_sale: YesNo
    sale: YesNo
    order_number: str | None = Field(default=None, min_length=1, max_length=30)
    outcome_detail: str | None = Field(default=None, min_length=1, max_length=80)
    reason_id: int | None = None
    consultant_id: int
    store_id: int
    coordinator_id: int
    regional_id: int

    @field_validator("cpf_cnpj")
    @classmethod
    def preserve_document_as_text(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def reason_rules(self):
        if not self.reason_id:
            raise ValueError("Motivo é obrigatório para o atendimento")
        if bool(self.opportunity) == bool(self.non_opportunity):
            raise ValueError("Informe uma oportunidade ou uma não oportunidade")
        if not self.outcome_detail:
            raise ValueError("Informe a classificação final do atendimento")
        if self.sale == YesNo.YES and not self.order_number:
            raise ValueError("Número da ordem é obrigatório para venda realizada")
        if self.sale == YesNo.NO and self.order_number:
            raise ValueError("Número da ordem deve ser informado apenas para venda realizada")
        if self.order_number and not self.order_number.isdigit():
            raise ValueError("Número da ordem deve conter apenas números")
        return self


class AttendancePatch(BaseModel):
    password_number: int | None = Field(default=None, ge=1)
    activity: str | None = Field(default=None, min_length=1, max_length=40)
    cpf_cnpj: str | None = Field(default=None, min_length=1, max_length=18)
    current_plan: str | None = Field(default=None, max_length=255)
    opportunity: str | None = Field(default=None, max_length=40)
    non_opportunity: str | None = Field(default=None, max_length=40)
    has_fiber_total: YesNo | None = None
    ftth_available: YesNo | None = None
    available_for_sale: YesNo | None = None
    sale: YesNo | None = None
    order_number: str | None = Field(default=None, min_length=1, max_length=30)
    outcome_detail: str | None = Field(default=None, min_length=1, max_length=80)
    reason_id: int | None = None
    consultant_id: int | None = None


class UnusedPasswordsOut(BaseModel):
    date: date
    store_id: int
    items: list[int]
    total: int


class AttendanceOut(ORMModel):
    id: int
    date: date
    password_number: int
    activity: str | None
    cpf_cnpj: str
    current_plan: str | None
    opportunity: str | None
    non_opportunity: str | None
    has_fiber_total: YesNo
    ftth_available: YesNo
    available_for_sale: YesNo
    sale: YesNo
    order_number: str | None
    outcome_detail: str | None
    reason_id: int | None
    consultant_id: int
    store_id: int
    coordinator_id: int
    regional_id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
