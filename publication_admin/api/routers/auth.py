from typing import Literal

from fastapi import APIRouter, Depends, Response, status
from loguru import logger
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from publication_admin.api.deps import SendEmail, get_db
from publication_admin.api.errors import (
    APIException,
    ErrorCode,
    ErrorResponse,
    ValidationErrorResponse,
)
from publication_admin.auth.email_auth import (
    AuthenticationError,
    EmailAuthenticator,
    EmailCodeIssuer,
)
from publication_admin.auth.jwt import JWTManager
from publication_admin.settings import settings

auth_router = APIRouter(tags=["auth"])


class GetCodeRequest(BaseModel):
    email: EmailStr


class AuthenticateRequest(BaseModel):
    email: EmailStr
    code: str


class AuthenticateResponse(BaseModel):
    access_token: str


@auth_router.post(
    "/get-code/",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    description="Send auth code to the user's email",
    responses={
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "model": ErrorResponse[Literal[ErrorCode.auth_email_code_rate_limit], None]
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorResponse},
    },
)
async def get_code(
    dto: GetCodeRequest,
    send_email: SendEmail,
    db: AsyncSession = Depends(get_db),
) -> None:
    code_issuer = EmailCodeIssuer(dto.email, db)

    if await code_issuer.is_sending_code_too_fast():
        raise APIException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code=ErrorCode.auth_email_code_rate_limit,
            message="You are sending email-code too often, try later",
        )

    email_code = await code_issuer.create_new_code()
    logger.info(f"Sent code {email_code.code} to {dto.email}")
    message = await code_issuer.get_email_message(email_code)
    send_email(message)


@auth_router.post(
    "/authenticate/",
    status_code=status.HTTP_200_OK,
    description="Sign-up or Sign-in using secret code",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse[Literal[ErrorCode.auth_invalid_credentials], None]},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorResponse},
    },
)
async def authenticate(dto: AuthenticateRequest, db: AsyncSession = Depends(get_db)) -> AuthenticateResponse:
    email_authenticator = EmailAuthenticator(dto.email, db)

    try:
        await email_authenticator.authenticate(dto.code)
    except AuthenticationError as e:
        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=ErrorCode.auth_invalid_credentials,
            message=str(e),
        ) from e

    user = await email_authenticator.get_user()

    if not user:
        user = await email_authenticator.register_user()

    jwt = JWTManager(secret_key=settings.secret_key)
    token = jwt.create_access_token(email=str(user.email), user_id=int(user.id))
    return AuthenticateResponse(access_token=token)
