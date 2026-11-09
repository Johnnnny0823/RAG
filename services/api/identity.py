"""Local account authentication for private research records."""

import hashlib
import hmac
import re
import secrets
from threading import BoundedSemaphore
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, SecretStr, field_validator
from sqlalchemy.exc import SQLAlchemyError

from services.api.db import engine

bearer = HTTPBearer(auto_error=False)
password_slots = BoundedSemaphore(2)
Credentials = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]


class IdentityError(Exception):
    pass


class IdentityUnavailable(Exception):
    pass


class AccountInput(BaseModel):
    email: str = Field(max_length=254)
    password: SecretStr = Field(min_length=12, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(
            r"[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9-]+(?:\.[a-z0-9-]+)+", value
        ):
            raise ValueError("Invalid email address")
        return value


class Account(BaseModel):
    id: UUID
    email: str


class AccessToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400


def password_hash(password: str, salt: bytes) -> bytes:
    with password_slots:
        return hashlib.scrypt(
            password.encode(),
            salt=salt,
            n=2**17,
            r=8,
            p=1,
            maxmem=160 * 1024**2,
            dklen=32,
        )


def register_account(payload: AccountInput) -> Account | None:
    salt = secrets.token_bytes(16)
    hashed = password_hash(payload.password.get_secret_value(), salt)
    with engine.begin() as conn:
        row = (
            conn.exec_driver_sql(
                """INSERT INTO users (email, password_salt, password_hash) VALUES (%s,%s,%s)
               ON CONFLICT (email) DO NOTHING RETURNING id, email""",
                (payload.email, salt, hashed),
            )
            .mappings()
            .one_or_none()
        )
    return Account.model_validate(row) if row else None


def login_account(payload: AccountInput) -> AccessToken:
    with engine.connect() as conn:
        row = conn.exec_driver_sql(
            "SELECT id, password_salt, password_hash FROM users WHERE email = %s",
            (payload.email,),
        ).one_or_none()
    salt = row.password_salt if row else bytes(16)
    expected = row.password_hash if row else bytes(32)
    valid = hmac.compare_digest(
        password_hash(payload.password.get_secret_value(), salt), expected
    )
    if not valid or row is None:
        raise IdentityError
    token = secrets.token_urlsafe(32)
    with engine.begin() as conn:
        conn.exec_driver_sql(
            "INSERT INTO auth_sessions (token_hash,user_id,expires_at) VALUES (%s,%s,now() + interval '24 hours')",
            (hashlib.sha256(token.encode()).digest(), row.id),
        )
    return AccessToken(access_token=token)


def require_account(credentials: Credentials) -> Account:
    if credentials is None or not re.fullmatch(
        r"[A-Za-z0-9_-]{43}", credentials.credentials
    ):
        raise IdentityError
    token_hash = hashlib.sha256(credentials.credentials.encode()).digest()
    try:
        with engine.connect() as conn:
            row = (
                conn.exec_driver_sql(
                    """SELECT u.id, u.email FROM auth_sessions s JOIN users u ON u.id = s.user_id
                   WHERE s.token_hash = %s AND s.expires_at > now()""",
                    (token_hash,),
                )
                .mappings()
                .one_or_none()
            )
    except SQLAlchemyError as error:
        raise IdentityUnavailable from error
    if row is None:
        raise IdentityError
    return Account.model_validate(row)
