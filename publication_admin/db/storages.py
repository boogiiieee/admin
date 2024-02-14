import typing
from uuid import UUID

from sqlalchemy import delete, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Avatar, Post, Topic


class BaseStorage:
    def __init__(self, db: AsyncSession):
        self.db = db


class AvatarsStorage(BaseStorage):
    async def create(self, **kwargs) -> Avatar:  # TODO: Proper typing for avatar input  # noqa: TD003, TD002
        """Add new avatar to the session"""
        avatar = Avatar(**kwargs)
        self.db.add(avatar)
        await self.db.flush()
        return avatar

    async def exists_for_user(self, user_id: int) -> bool:
        row = await self.db.execute(select(exists().where(Avatar.user_id == user_id)))
        return row.scalar()

    async def get_by_user_id(self, user_id: int) -> Avatar | None:
        rows = await self.db.execute(select(Avatar).where(Avatar.user_id == user_id).limit(1))
        return rows.scalars().first()

    async def delete_avatar(self, avatar_id: int, user_id: int) -> typing.Optional[int]:
        """
        Delete avatar by avatar_id and user_id
        """
        result = await self.db.execute(
            delete(Avatar).where(Avatar.id == avatar_id, Avatar.user_id == user_id).returning(Avatar.id)
        )
        deleted_avatar_id = result.scalar()
        await self.db.commit()
        return deleted_avatar_id


class TopicsStorage(BaseStorage):
    async def all(self):
        rows = await self.db.execute(select(Topic))
        return rows.scalars().all()

    async def exists(self, name: str) -> bool:
        row = await self.db.execute(select(exists().where(Topic.name == name)))
        return row.scalar()

    async def add_new_topics(self, topics: list[str]):
        """Add to the session topics that does not exist in the database"""
        for topic_name in topics:
            if not await self.exists(topic_name):
                self.db.add(Topic(name=topic_name))


class PostStorage(BaseStorage):
    async def create(self, avatar_id: int, post_text: str, images: typing.List[str]) -> Post:
        """
        Create new post
        """
        post = Post(avatar_id=avatar_id, post_text=post_text, images=images)
        self.db.add(post)
        await self.db.commit()
        await self.db.flush()
        return post

    async def get_posts_by_avatar(self, avatar_id: int, post_uuid: UUID = None):
        """
        Get posts by avatar. If post_uuid is provided, get a specific post.
        """
        query = select(Post).where(Post.avatar_id == avatar_id)
        if post_uuid:
            query = query.where(Post.uuid == post_uuid)
        result = await self.db.execute(query)
        posts = result.scalars().all()
        return posts

    async def delete_posts(self, avatar_id: int, post_uuid: UUID) -> typing.Optional[UUID]:
        """
        Delete post by post_id
        """
        result = await self.db.execute(
            delete(Post).where(Post.avatar_id == avatar_id, Post.uuid == post_uuid).returning(Post.uuid)
        )
        deleted_post_uuid = result.scalar()
        await self.db.commit()
        return deleted_post_uuid
