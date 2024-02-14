from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from publication_admin.api.deps import CurrentUser, get_db
from publication_admin.api.errors import APIException, ErrorCode, UnauthorizedErrorResponse
from publication_admin.db.storages import AvatarsStorage, PostStorage

posts_router = APIRouter(tags=["post"])


class DeletedPostResponse(BaseModel):
    deleted_post_uuid: UUID


class PostCreate(BaseModel):
    post_text: str | None
    images: list[str]


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uuid: UUID
    avatar_id: int
    post_text: str = ""
    images: list[str] = []
    created_at: datetime


@posts_router.get(
    "/",
    description="Get posts for user",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": UnauthorizedErrorResponse,
            "description": "Invalid or expired JWT",
        }
    },
)
async def get_posts(current_user: CurrentUser, db: AsyncSession = Depends(get_db)) -> List[PostResponse]:
    avatar_storage = AvatarsStorage(db)
    current_avatar = await avatar_storage.get_by_user_id(current_user.id)
    post_storage = PostStorage(db)
    posts = await post_storage.get_posts_by_avatar(avatar_id=current_avatar.id)
    return [PostResponse.model_validate(post) for post in posts]


@posts_router.get(
    "/{post_uuid}",
    description="Get single post by ID",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": UnauthorizedErrorResponse,
            "description": "Invalid or expired JWT",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Post not found",
        },
    },
)
async def get_post_by_id(
    post_uuid: UUID, current_user: CurrentUser, db: AsyncSession = Depends(get_db)
) -> PostResponse:
    avatar_storage = AvatarsStorage(db)
    current_avatar = await avatar_storage.get_by_user_id(current_user.id)
    post_storage = PostStorage(db)
    post = await post_storage.get_posts_by_avatar(avatar_id=current_avatar.id, post_uuid=post_uuid)
    if not post:
        raise APIException(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=ErrorCode.common_not_found,
            message="Post not found",
        )
    return PostResponse.model_validate(post[0])


@posts_router.post(
    "/",
    description="Create post",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": UnauthorizedErrorResponse,
            "description": "Invalid or expired JWT",
        },
    },
)
async def create_post(dto: PostCreate, current_user: CurrentUser, db: AsyncSession = Depends(get_db)) -> PostResponse:
    avatar_storage = AvatarsStorage(db)
    current_avatar = await avatar_storage.get_by_user_id(current_user.id)
    post_storage = PostStorage(db)
    new_post = await post_storage.create(avatar_id=current_avatar.id, post_text=dto.post_text, images=dto.images)
    return PostResponse.model_validate(new_post)


@posts_router.delete(
    "/{post_uuid}",
    description="Delete a post",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": UnauthorizedErrorResponse,
            "description": "Invalid or expired JWT",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Post not found",
        },
    },
)
async def delete_post(
    post_uuid: UUID, current_user: CurrentUser, db: AsyncSession = Depends(get_db)
) -> DeletedPostResponse:
    avatar_storage = AvatarsStorage(db)
    current_avatar = await avatar_storage.get_by_user_id(current_user.id)
    post_storage = PostStorage(db)
    deleted_post = await post_storage.delete_posts(avatar_id=current_avatar.id, post_uuid=post_uuid)
    if not deleted_post:
        raise APIException(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=ErrorCode.common_not_found,
            message="Post not found",
        )
    return DeletedPostResponse(deleted_post_uuid=deleted_post)
