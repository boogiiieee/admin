from fastapi import APIRouter, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError, StarletteHTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from publication_admin.settings import settings

from .errors import APIException, ErrorCode, ErrorResponse
from .routers.auth import auth_router
from .routers.avatars import avatars_router
from .routers.files import files_router
from .routers.meta import meta_router
from .routers.posts import posts_router
from .routers.topics import topics_router
from .routers.users import users_router

app = FastAPI(title="publication_admin API")
api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router, prefix="/auth")
api_router.include_router(users_router, prefix="/users")
api_router.include_router(meta_router, prefix="/meta")
api_router.include_router(avatars_router, prefix="/avatars")
api_router.include_router(topics_router, prefix="/topics")
api_router.include_router(files_router, prefix="/files")
api_router.include_router(posts_router, prefix="/posts")
app.include_router(api_router)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(APIException)
async def api_exception_handler(_: Request, exc: APIException):
    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers,
        content=ErrorResponse(
            error_code=exc.error_code,
            message=exc.message,
            details=exc.detail,
        ).model_dump(),
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_: Request, exc: StarletteHTTPException):
    """
    Map FastAPI exceptions to the API error format
    """
    error_code = ErrorCode.common_error

    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        error_code = ErrorCode.auth_unauthorized
    elif exc.status_code == status.HTTP_403_FORBIDDEN:
        error_code = ErrorCode.auth_forbidden

    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers,
        content=ErrorResponse(
            error_code=error_code,
            message=exc.detail if isinstance(exc.detail, str) else "Unknown error",
            details=exc.detail,
        ).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(_: Request, exc: RequestValidationError):
    message = "Request data is not valid"

    if exc.errors():
        message = "".join(error["msg"] for error in exc.errors())

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error_code=ErrorCode.common_validation_error,
            message=message,
            details=exc.errors(),
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def base_exception_handler(_: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error_code=ErrorCode.common_internal_error,
            message="Unknown error",
            details=f"{exc}" if settings.is_local_env() else None,
        ).model_dump(),
    )
