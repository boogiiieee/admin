from typing import Annotated, Callable

from fastapi import BackgroundTasks, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi_mail import FastMail, MessageSchema
from sqlalchemy.ext.asyncio import AsyncSession

from publication_admin.auth.jwt import JWTError, JWTManager
from publication_admin.db.engine import AsyncSessionFactory
from publication_admin.db.models import User
from publication_admin.media_storage.s3 import S3MediaStorage
from publication_admin.services.avatars_ai import MLImages, MLText
from publication_admin.settings import settings

from .errors import APIUnauthorizedException

bearer_token_scheme = HTTPBearer(auto_error=False)


async def get_db():
    async with AsyncSessionFactory() as session:
        yield session


async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(bearer_token_scheme),
    session: AsyncSession = Depends(get_db),
) -> User:
    if not token:
        raise APIUnauthorizedException("No credentials")

    try:
        jwt = JWTManager(secret_key=settings.secret_key)
        user_id = jwt.get_user_id(token.credentials)
    except JWTError as e:
        raise APIUnauthorizedException(f"Could not validate credentials: {e}") from e

    user = await session.get(User, user_id)
    if not user:
        raise APIUnauthorizedException("User is invalid or deleted")
    return user


async def require_auth(current_user: User = Depends(get_current_user)):
    pass


async def send_email(background_tasks: BackgroundTasks):
    def send(message: MessageSchema):
        if not settings.is_local_env():
            mail_service = FastMail(settings.mail)
            background_tasks.add_task(mail_service.send_message, message)

    return send


async def media_storage() -> S3MediaStorage:
    return S3MediaStorage()


async def get_ml_text_service() -> MLText:
    return MLText(base_url=settings.ml_text_service_url)


async def get_ml_images_service() -> MLImages:
    return MLImages(base_url=settings.ml_images_service_url)


BearerToken = Annotated[HTTPAuthorizationCredentials, Depends(bearer_token_scheme)]
DBSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
SendEmail = Annotated[Callable[[MessageSchema], None], Depends(send_email)]
MediaStorage = Annotated[S3MediaStorage, Depends(media_storage)]
MLImagesService = Annotated[MLImages, Depends(get_ml_images_service)]
MLTextService = Annotated[MLText, Depends(get_ml_text_service)]
