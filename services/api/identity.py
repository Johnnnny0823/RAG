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


class LoginThrottled(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after


LOGIN_FAILURE_LIMIT = 5
LOGIN_FAILURE_WINDOW = "15 minutes"


class PasswordConfirmation(BaseModel):
    password: SecretStr = Field(min_length=12, max_length=128)


class AccountInput(PasswordConfirmation):
    email: str = Field(max_length=254)

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
    # Keyed by the submitted address, so unknown accounts throttle the same way.
    key = hashlib.sha256(payload.email.encode()).digest()
    with engine.connect() as conn:
        retry_after = conn.exec_driver_sql(
            f"""SELECT ceil(extract(epoch FROM failed_at + interval '{LOGIN_FAILURE_WINDOW}' - now()))
                FROM login_failures
                WHERE email_hash = %s AND failed_at > now() - interval '{LOGIN_FAILURE_WINDOW}'
                ORDER BY failed_at DESC OFFSET %s LIMIT 1""",
            (key, LOGIN_FAILURE_LIMIT - 1),
        ).scalar_one_or_none()
        if retry_after is not None:
            raise LoginThrottled(max(1, int(retry_after)))
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
        with engine.begin() as conn:
            conn.exec_driver_sql(
                f"DELETE FROM login_failures WHERE failed_at <= now() - interval '{LOGIN_FAILURE_WINDOW}'"
            )
            conn.exec_driver_sql(
                "INSERT INTO login_failures (email_hash) VALUES (%s)", (key,)
            )
        raise IdentityError
    token = secrets.token_urlsafe(32)
    with engine.begin() as conn:
        conn.exec_driver_sql("DELETE FROM login_failures WHERE email_hash = %s", (key,))
        conn.exec_driver_sql(
            "INSERT INTO auth_sessions (token_hash,user_id,expires_at) VALUES (%s,%s,now() + interval '24 hours')",
            (hashlib.sha256(token.encode()).digest(), row.id),
        )
    return AccessToken(access_token=token)


def credential_digest(credentials: HTTPAuthorizationCredentials | None) -> bytes:
    if credentials is None or not re.fullmatch(
        r"[A-Za-z0-9_-]{43}", credentials.credentials
    ):
        raise IdentityError
    return hashlib.sha256(credentials.credentials.encode()).digest()


def revoke_session(credentials: Credentials) -> None:
    token_hash = credential_digest(credentials)
    try:
        with engine.begin() as conn:
            conn.exec_driver_sql(
                "DELETE FROM auth_sessions WHERE token_hash = %s", (token_hash,)
            )
    except SQLAlchemyError as error:
        raise IdentityUnavailable from error


def delete_account(account: Account, payload: PasswordConfirmation) -> bool:
    with engine.connect() as conn:
        row = conn.exec_driver_sql(
            "SELECT password_salt, password_hash FROM users WHERE id=%s", (account.id,)
        ).one_or_none()
    if row is None:
        raise IdentityError
    if not hmac.compare_digest(
        password_hash(payload.password.get_secret_value(), row.password_salt),
        row.password_hash,
    ):
        return False

    with engine.begin() as conn:
        params = (account.id,)
        locked = conn.exec_driver_sql(
            "SELECT id FROM users WHERE id=%s AND password_hash=%s FOR UPDATE",
            (account.id, row.password_hash),
        ).scalar_one_or_none()
        if locked is None:
            raise IdentityError
        conn.exec_driver_sql(
            "SELECT id FROM projects WHERE owner_user_id=%s ORDER BY id FOR UPDATE",
            params,
        ).all()
        conn.exec_driver_sql("DELETE FROM search_runs WHERE user_id=%s", params)
        conn.exec_driver_sql(
            """DELETE FROM sessions s USING projects p
               WHERE s.project_id=p.id AND p.owner_user_id=%s""",
            params,
        )
        conn.exec_driver_sql(
            """DELETE FROM saved_patents b USING projects p
               WHERE b.project_id=p.id AND p.owner_user_id=%s""",
            params,
        )
        conn.exec_driver_sql("DELETE FROM projects WHERE owner_user_id=%s", params)
        conn.exec_driver_sql("DELETE FROM auth_sessions WHERE user_id=%s", params)
        conn.exec_driver_sql(
            "DELETE FROM login_failures WHERE email_hash=%s",
            (hashlib.sha256(account.email.encode()).digest(),),
        )
        conn.exec_driver_sql("DELETE FROM users WHERE id=%s", params)
    return True


def require_account(credentials: Credentials) -> Account:
    token_hash = credential_digest(credentials)
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
