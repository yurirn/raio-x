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
    cpf_cnpj: str = Field(min_length=1, max_length=18)
    current_plan: str | None = Field(default=None, max_length=255)
    ftth_available: YesNo
    available_for_sale: YesNo
    sale: YesNo
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
        if self.sale == YesNo.NO and not self.reason_id:
            raise ValueError("Motivo é obrigatório quando não houver venda")
        if self.sale == YesNo.YES and self.reason_id:
            raise ValueError("Motivo deve ficar vazio quando houver venda")
        return self


class AttendancePatch(BaseModel):
    password_number: int | None = Field(default=None, ge=1)
    cpf_cnpj: str | None = Field(default=None, min_length=1, max_length=18)
    current_plan: str | None = Field(default=None, max_length=255)
    ftth_available: YesNo | None = None
    available_for_sale: YesNo | None = None
    sale: YesNo | None = None
    reason_id: int | None = None
    consultant_id: int | None = None


class AttendanceOut(ORMModel):
    id: int
    date: date
    password_number: int
    cpf_cnpj: str
    current_plan: str | None
    ftth_available: YesNo
    available_for_sale: YesNo
    sale: YesNo
    reason_id: int | None
    consultant_id: int
    store_id: int
    coordinator_id: int
    regional_id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
