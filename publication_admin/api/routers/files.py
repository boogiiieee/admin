import uuid

from fastapi import APIRouter, Depends, UploadFile, status
from pydantic import BaseModel, computed_field

from publication_admin.api.deps import MediaStorage, require_auth
from publication_admin.api.errors import (
    APIException,
    APIValidationException,
    ErrorCode,
    UnauthorizedErrorResponse,
    ValidationErrorResponse,
)
from publication_admin.media_storage.s3 import UploadError
from publication_admin.settings import settings

ALLOWED_IMAGE_CONTENT_TYPE = "image/jpeg"

files_router = APIRouter(dependencies=[Depends(require_auth)], tags=["files"])


class MediaStorageImage(BaseModel):
    file_id: str

    @computed_field
    def url(self) -> str:
        return (
            f"{settings.media_storage.media_storage_url}/"
            f"{settings.media_storage.media_storage_bucket}/"
            f"{self.file_id}"
        )


@files_router.post(
    "/image/upload/",
    status_code=status.HTTP_200_OK,
    description="Uploading file to media storage",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": UnauthorizedErrorResponse,
            "description": "Invalid or expired JWT",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ValidationErrorResponse,
            "description": "Invalid content type or file size or file is missing",
        },
    },
)
async def upload(file: UploadFile, media_storage: MediaStorage) -> MediaStorageImage:
    if file.content_type != ALLOWED_IMAGE_CONTENT_TYPE:
        raise APIValidationException(
            message=f"Invalid content type, only {ALLOWED_IMAGE_CONTENT_TYPE} is allowed",
        )
    if file.size > settings.image_size_limit:
        raise APIValidationException(
            message=f"Too large file, limit is {settings.image_size_limit}, " f"actual size is {file.size}",
        )

    file_id = f"pubadmin/user-content/{uuid.uuid4()}.jpeg"
    try:
        media_storage.upload_file(file_id, content=file.file)
    except UploadError as e:
        raise APIException(
            status_code=500,
            message=f"File upload error, details: {e}",
            error_code=ErrorCode.common_internal_error,
        ) from e
    return MediaStorageImage(file_id=file_id)
