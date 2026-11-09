"""Local registration and login."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.exc import SQLAlchemyError

from services.api.identity import (
    AccessToken,
    Account,
    AccountInput,
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


@router.post("/auth/login", response_model=AccessToken)
def login(payload: AccountInput, response: Response):
    try:
        token = login_account(payload)
    except SQLAlchemyError:
        return unavailable()
    response.headers["Cache-Control"] = "no-store"
    return token


@router.get("/me", response_model=Account)
def me(account: Annotated[Account, Depends(require_account)], response: Response):
    response.headers["Cache-Control"] = "no-store"
    return account


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
