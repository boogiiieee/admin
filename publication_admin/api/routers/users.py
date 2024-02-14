from fastapi import APIRouter, status
from pydantic import BaseModel

from publication_admin.api.deps import CurrentUser
from publication_admin.api.errors import UnauthorizedErrorResponse

users_router = APIRouter(tags=["user"])


class UserResponse(BaseModel):
    id: int
    email: str


@users_router.get(
    "/me/",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": UnauthorizedErrorResponse,
            "description": "Invalid or expired JWT",
        }
    },
)
async def get_user(current_user: CurrentUser) -> UserResponse:
    return UserResponse(id=current_user.id, email=current_user.email)
