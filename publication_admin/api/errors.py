from enum import StrEnum
from typing import Any, Generic, List, Literal, TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel, Field


class ErrorCode(StrEnum):
    common_error = "common.error"
    common_validation_error = "common.validation_error"
    common_internal_error = "common.internal_error"
    common_not_found = "common.not_found"

    auth_email_code_rate_limit = "auth.email_code_rate_limit"
    auth_forbidden = "auth.forbidden"
    auth_invalid_credentials = "auth.invalid_credentials"
    auth_unauthorized = "auth.unauthorized"


class APIException(HTTPException):
    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: Any = None,
        headers: dict[str, str] | None = None,
    ):
        super().__init__(status_code=status_code, headers=headers)
        self.error_code = error_code
        self.message = message
        self.detail = detail


class APIUnauthorizedException(APIException):
    def __init__(self, message: str = "Could not validate credentials"):
        super().__init__(
            error_code=ErrorCode.auth_unauthorized,
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
        )


class APINotFoundException(APIException):
    def __init__(self, message: str = "Entity not found"):
        super().__init__(
            error_code=ErrorCode.common_not_found,
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class APIValidationException(APIException):
    def __init__(self, message: str = "Validation error", detail: Any = None):
        super().__init__(
            error_code=ErrorCode.common_validation_error,
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )


E = TypeVar("E", bound=ErrorCode)
D = TypeVar("D")


class ErrorResponse(BaseModel, Generic[E, D]):
    """Generic error response"""

    error_code: E
    message: str
    details: D


class ValidationErrorDetails(BaseModel):
    """
    Information about all the validation errors and how they happened.
    """

    type: str = Field(
        ...,
        description=(
            """
            The type of error that occurred, this is an identifier designed for
            programmatic use that will change rarely or never.

            `type` is unique for each error message, and can hence be used as an identifier
             to build custom error messages.
            """
        ),
    )

    loc: tuple[int | str, ...] = Field(
        ...,
        description="Tuple of strings and ints identifying where in the schema the error occurred.",
    )
    msg: str = Field(..., description="A human readable error message.")

    input: Any = Field(..., description="The input data at this `loc` that caused the error.")

    ctx: dict[str, Any] = Field(
        ...,
        description=(
            """
            Values which are required to render the error message, 
            and could hence be useful in rendering custom error messages.
            Also useful for passing custom error data forward.
            """
        ),
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "type": "value_error",
                "loc": ["body", "email"],
                "msg": "value is not a valid email address: "
                "The email address is not valid. It must have exactly one @-sign.",
                "input": "inv@lid_email@example.com",
                "ctx": {"reason": "The email address is not valid. It must have exactly one @-sign."},
            }
        }
    }


CommonErrorResponse = ErrorResponse[Literal[ErrorCode.common_error], None]

ValidationErrorResponse = ErrorResponse[Literal[ErrorCode.common_validation_error], List[ValidationErrorDetails] | None]
ValidationErrorWithoutDetailsResponse = ErrorResponse[Literal[ErrorCode.common_validation_error], None]

UnauthorizedErrorResponse = ErrorResponse[Literal[ErrorCode.auth_unauthorized], None]
NotFoundErrorResponse = ErrorResponse[Literal[ErrorCode.common_not_found], None]
