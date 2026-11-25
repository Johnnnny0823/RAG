"""Local registration and login."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.exc import SQLAlchemyError

from services.api.admin_ingestion import is_ingestion_admin
from services.api.identity import (
    AccessToken,
    Account,
    AccountInput,
    LoginThrottled,
    PasswordConfirmation,
    delete_account,
    login_account,
    register_account,
    require_account,
    revoke_session,
)
from services.api.patents import (
    PatentErrorEnvelope,
    PatentRoute,
    api_error,
    unavailable,
)

router = APIRouter(
    prefix="/api/v1",
    tags=["accounts"],
    route_class=PatentRoute,
    responses={code: {"model": PatentErrorEnvelope} for code in (401, 422, 503)},
)


@router.post(
    "/auth/register",
    response_model=Account,
    status_code=201,
    responses={409: {"model": PatentErrorEnvelope}},
)
def register(payload: AccountInput):
    try:
        account = register_account(payload)
    except SQLAlchemyError:
        return unavailable()
    if account is None:
        return api_error(409, "ACCOUNT_EXISTS", "此帳號已註冊。")
    return account


@router.post(
    "/auth/login",
    response_model=AccessToken,
    responses={429: {"model": PatentErrorEnvelope}},
)
def login(payload: AccountInput, response: Response):
    try:
        token = login_account(payload)
    except LoginThrottled as throttled:
        limited = api_error(429, "LOGIN_THROTTLED", "登入失敗次數過多，請稍後再試。")
        limited.headers["Retry-After"] = str(throttled.retry_after)
        limited.headers["Cache-Control"] = "no-store"
        return limited
    except SQLAlchemyError:
        return unavailable()
    response.headers["Cache-Control"] = "no-store"
    return token


class AccountProfile(Account):
    can_monitor_ingestion: bool


@router.get("/me", response_model=AccountProfile)
def me(account: Annotated[Account, Depends(require_account)], response: Response):
    response.headers["Cache-Control"] = "no-store"
    return AccountProfile(
        **account.model_dump(), can_monitor_ingestion=is_ingestion_admin(account.id)
    )


@router.delete("/me", status_code=204, responses={403: {"model": PatentErrorEnvelope}})
def remove_account(
    payload: PasswordConfirmation, account: Annotated[Account, Depends(require_account)]
):
    try:
        deleted = delete_account(account, payload)
    except SQLAlchemyError:
        return unavailable()
    if not deleted:
        return api_error(
            403, "PASSWORD_CONFIRMATION_FAILED", "密碼驗證失敗，帳號未刪除。"
        )
    return Response(status_code=204, headers={"Cache-Control": "no-store"})


@router.post("/auth/logout", status_code=204)
def logout(_: Annotated[None, Depends(revoke_session)]):
    return Response(status_code=204, headers={"Cache-Control": "no-store"})
