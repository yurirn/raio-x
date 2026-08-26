from datetime import datetime, timedelta, timezone
from functools import lru_cache

import jwt
from fastapi import HTTPException, status
from pwdlib import PasswordHash
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://raiox:raiox@localhost:5432/raiox"
    jwt_secret: str = "local-development-secret-change-me"
    jwt_expire_minutes: int = 480
    cors_origins: str = (
        "http://localhost:3000,http://localhost:3001,http://localhost:5173,"
        "http://127.0.0.1:3000,http://127.0.0.1:3001,http://127.0.0.1:5173"
    )
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip().rstrip("/") for origin in self.cors_origins.split(",") if origin.strip()
        ]


@lru_cache
def settings() -> Settings:
    return Settings()


password_hash = PasswordHash.recommended()


def hash_password(value: str) -> str:
    return password_hash.hash(value)


def verify_password(value: str, hashed: str) -> bool:
    return password_hash.verify(value, hashed)


def create_token(user_id: int, role: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings().jwt_expire_minutes)
    return jwt.encode(
        {"sub": str(user_id), "role": role, "exp": expires},
        settings().jwt_secret,
        algorithm="HS256",
    )


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings().jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou expirado"
        ) from exc
