from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, constr
from sqlalchemy.ext.asyncio import AsyncSession

from publication_admin.api.deps import (
    CurrentUser,
    DBSession,
    MLImagesService,
    MLTextService,
    get_current_user,
    get_db,
)
from publication_admin.api.errors import (
    APIException,
    APINotFoundException,
    CommonErrorResponse,
    ErrorCode,
    NotFoundErrorResponse,
    UnauthorizedErrorResponse,
    ValidationErrorResponse,
)
from publication_admin.db.models import InitStatus
from publication_admin.db.storages import AvatarsStorage, TopicsStorage
from publication_admin.services.avatars_ai.ml_images.dto import TaskStatus
from publication_admin.services.avatars_ai.service import ServiceError

avatars_router = APIRouter(dependencies=[Depends(get_current_user)], tags=["avatar"])

ml_service_unavailable = APIException(
    error_code=ErrorCode.common_error,
    message="Resource is not available now, try later",
    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
)


class AvatarResponse(BaseModel):
    name: str
    text: str
    topics: list[constr(strip_whitespace=True)]
    images: list[str]
    profile_picture: str | None


class CreateAvatarRequest(BaseModel):
    name: str
    text: str
    topics: list[constr(strip_whitespace=True)]
    images: list[str]

    model_config = ConfigDict(str_strip_whitespace=True)


class ModifyAvatarRequest(BaseModel):
    name: str
    text: str
    topics: list[constr(strip_whitespace=True)]

    model_config = ConfigDict(str_strip_whitespace=True)


class GenerateBioRequest(BaseModel):
    name: str
    text: str
    topics: list[str]


class GeneratedBioResponse(BaseModel):
    text: str


class AvatarInitResponse(BaseModel):
    status: InitStatus


class GenerateProfileImageRequest(BaseModel):
    style: str


class GenerateProfileImageResponse(BaseModel):
    task_id: str


class ProfileImagesStatusResponse(BaseModel):
    task_id: str
    status: TaskStatus
    image_path: str | None
    image_url: str | None


class DeletedAvatarResponse(BaseModel):
    avatar_id: int


@avatars_router.get(
    "/current/",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": UnauthorizedErrorResponse,
            "description": "Invalid or expired JWT",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": NotFoundErrorResponse,
            "description": "User do not have any avatar",
        },
    },
)
async def get_current_avatar(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> AvatarResponse:
    avatar_storage = AvatarsStorage(db)
    current_avatar = await avatar_storage.get_by_user_id(current_user.id)

    if not current_avatar:
        raise APINotFoundException()

    return AvatarResponse(
        name=current_avatar.name,
        text=current_avatar.text,
        topics=current_avatar.topics,
        images=current_avatar.images,
        profile_picture=None,
    )


@avatars_router.post(
    "/",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": UnauthorizedErrorResponse,
            "description": "Invalid or expired JWT",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": NotFoundErrorResponse,
            "description": "User do not have any avatar",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorResponse},
        status.HTTP_501_NOT_IMPLEMENTED: {
            "model": CommonErrorResponse,
            "description": "Multiple avatars not supported at the moment",
        },
    },
)
async def create_avatar(
    dto: CreateAvatarRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> AvatarResponse:
    avatar_storage = AvatarsStorage(db)

    if await avatar_storage.exists_for_user(current_user.id):
        raise APIException(
            error_code=ErrorCode.common_error,
            message="Multiple avatars not supported at the moment",
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
        )

    avatar = await avatar_storage.create(
        user_id=current_user.id,
        name=dto.name.strip(),
        text=dto.text.strip(),
        topics=dto.topics,
        images=dto.images,
    )
    await db.commit()

    return AvatarResponse(
        name=avatar.name,
        text=avatar.text,
        topics=avatar.topics,
        images=avatar.images,
        profile_picture=None,
    )


@avatars_router.patch(
    "/current/",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": UnauthorizedErrorResponse,
            "description": "Invalid or expired JWT",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": NotFoundErrorResponse,
            "description": "User do not have any avatar",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorResponse},
    },
)
async def patch_avatar(
    dto: ModifyAvatarRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> AvatarResponse:
    avatar_storage = AvatarsStorage(db)
    avatar = await avatar_storage.get_by_user_id(current_user.id)

    if not avatar:
        raise APINotFoundException()

    avatar.name = dto.name.strip()
    avatar.text = dto.text.strip()
    avatar.topics = dto.topics
    await TopicsStorage(db).add_new_topics(dto.topics)
    await db.commit()

    return AvatarResponse(
        name=avatar.name,
        text=avatar.text,
        topics=avatar.topics,
        images=avatar.images,
        profile_picture=None,
    )


@avatars_router.delete(
    "/current/",
    description="Delete current avatar",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": UnauthorizedErrorResponse,
            "description": "Invalid or expired JWT",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Avatar not found",
        },
    },
)
async def delete_avatar(current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    avatar_storage = AvatarsStorage(db)
    current_avatar = await avatar_storage.get_by_user_id(current_user.id)
    if current_avatar is None:
        raise APIException(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=ErrorCode.common_not_found,
            message="Avatar not found",
        )
    deleted_avatar_id = await avatar_storage.delete_avatar(avatar_id=current_avatar.id, user_id=current_user.id)
    return DeletedAvatarResponse(avatar_id=deleted_avatar_id)


@avatars_router.post(
    "/generate-bio/",
    description="Generate avatar about text",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": UnauthorizedErrorResponse,
            "description": "Invalid or expired JWT",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorResponse},
    },
)
async def generate_bio(
    dto: GenerateBioRequest,
    ml_text_service: MLTextService,
) -> GeneratedBioResponse:
    try:
        response = await ml_text_service.bio(name=dto.name, text=dto.text, topics=", ".join(dto.topics))
    except ServiceError as e:
        raise ml_service_unavailable from e

    return GeneratedBioResponse(text=response.text)


@avatars_router.post(
    "/current/init/",
    description="Run avatar adapter pipeline in background",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": UnauthorizedErrorResponse,
            "description": "Invalid or expired JWT",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": NotFoundErrorResponse,
            "description": "User do not have any avatar",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": CommonErrorResponse,
            "description": "Avatar init was already triggered",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": CommonErrorResponse,
            "description": "ML service unavailable",
        },
    },
)
async def init_avatar(
    current_user: CurrentUser, ml_images_service: MLImagesService, db_session: DBSession
) -> AvatarInitResponse:
    avatar_storage = AvatarsStorage(db_session)
    avatar = await avatar_storage.get_by_user_id(current_user.id)

    if not avatar:
        raise APINotFoundException()

    if avatar.init_status != InitStatus.CREATED:
        raise APIException(
            error_code=ErrorCode.common_error,
            message="Avatar initialization was already triggered",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    avatar.set_random_lora_name()
    try:
        response = await ml_images_service.post_init_persona_task(
            lora_name=avatar.lora_name,
            s3_paths=avatar.images,
        )
    except ServiceError as e:
        raise ml_service_unavailable from e

    avatar.init_persona_task_id = response.task_id
    avatar.init_status = InitStatus.PENDING
    await db_session.commit()
    return AvatarInitResponse(status=avatar.init_status)


@avatars_router.get(
    "/current/init-status/",
    description="Get status of avatar adapter training",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": UnauthorizedErrorResponse,
            "description": "Invalid or expired JWT",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": NotFoundErrorResponse,
            "description": "User do not have any avatar",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": CommonErrorResponse,
            "description": "ML service unavailable",
        },
    },
)
async def init_status(
    current_user: CurrentUser, ml_images_service: MLImagesService, db_session: DBSession
) -> AvatarInitResponse:
    avatar_storage = AvatarsStorage(db_session)
    avatar = await avatar_storage.get_by_user_id(current_user.id)

    if not avatar:
        raise APINotFoundException()

    if avatar.init_status == InitStatus.PENDING:
        try:
            response = await ml_images_service.get_init_persona_task(avatar.init_persona_task_id)
        except ServiceError as e:
            raise ml_service_unavailable from e

        if response.status.is_success() and response.lora_s3_path:
            avatar.lora_path = response.lora_s3_path
            avatar.init_status = InitStatus.SUCCESS
            await db_session.commit()

    return AvatarInitResponse(status=avatar.init_status)


@avatars_router.post(
    "/current/generate-profile-image/",
    description="Generate avatar profile picture",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": CommonErrorResponse,
            "description": "Avatar is not initialized",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": UnauthorizedErrorResponse,
            "description": "Invalid or expired JWT",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": NotFoundErrorResponse,
            "description": "User do not have any avatar",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": CommonErrorResponse,
            "description": "ML service unavailable",
        },
    },
)
async def generate_profile_images(
    dto_in: GenerateProfileImageRequest,
    current_user: CurrentUser,
    ml_images_service: MLImagesService,
    db_session: DBSession,
):
    avatar_storage = AvatarsStorage(db_session)
    avatar = await avatar_storage.get_by_user_id(current_user.id)
    if not avatar:
        raise APINotFoundException()
    if avatar.init_status != InitStatus.SUCCESS:
        raise APIException(
            error_code=ErrorCode.common_error,
            message="Avatar is not initialized",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        response = await ml_images_service.create_text_to_picture_task(
            lora_name=avatar.lora_name,
            lora_s3_path=avatar.lora_path,
            caption="Create profile picture",
        )
    except ServiceError as e:
        raise ml_service_unavailable from e

    return GenerateProfileImageResponse(task_id=response.task_id)


@avatars_router.get(
    "/current/profile-images-status/",
    description="Get status of profile picture generation",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": UnauthorizedErrorResponse,
            "description": "Invalid or expired JWT",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": CommonErrorResponse,
            "description": "ML service unavailable",
        },
    },
)
async def profile_images_status(
    task_id: str,
    ml_images_service: MLImagesService,
) -> ProfileImagesStatusResponse:
    try:
        response = await ml_images_service.get_text_to_picture_task(task_id)
    except ServiceError as e:
        raise ml_service_unavailable from e

    return ProfileImagesStatusResponse(
        task_id=response.task_id,
        status=response.status,
        image_path=response.image_path,
        image_url="",
    )
