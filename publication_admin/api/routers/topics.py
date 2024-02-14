from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from publication_admin.api.deps import get_current_user, get_db
from publication_admin.api.errors import UnauthorizedErrorResponse
from publication_admin.db.storages import TopicsStorage

topics_router = APIRouter(dependencies=[Depends(get_current_user)], tags=["topic"])


class TopicResponse(BaseModel):
    name: str


@topics_router.get(
    "/",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": UnauthorizedErrorResponse,
            "description": "Invalid or expired JWT",
        },
    },
)
async def get_all(db: AsyncSession = Depends(get_db)) -> list[TopicResponse]:
    topics = await TopicsStorage(db).all()
    return [TopicResponse(name=topic.name) for topic in topics]
