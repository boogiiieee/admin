import datetime
import json
import random
from uuid import uuid4

from fastapi import status
from httpx import AsyncClient
from pytest_mock import MockerFixture

from publication_admin.api.routers.posts import PostResponse
from publication_admin.db.models import Avatar, Post

PostStoragePath = "publication_admin.api.routers.posts.PostStorage"
AvatarsStoragePath = "publication_admin.api.routers.posts.AvatarsStorage"


class TestGetPosts:
    async def test_auth_required(self, client: AsyncClient):
        response = await client.get("/api/posts/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_get_posts(self, client: AsyncClient, mocker: MockerFixture, john_doe):
        avatar_id = random.randint(1, 20)
        mocked_posts = [
            Post(
                uuid=uuid4(),
                avatar_id=avatar_id,
                post_text="text1",
                images=["link1", "link2"],
                created_at=datetime.datetime.now(),
            ),
            Post(
                uuid=uuid4(),
                avatar_id=avatar_id,
                post_text="text2",
                images=[],
                created_at=datetime.datetime.now(),
            ),
            Post(
                uuid=uuid4(),
                avatar_id=avatar_id,
                post_text="text3",
                images=["link3"],
                created_at=datetime.datetime.now(),
            ),
        ]
        mocker.patch(f"{PostStoragePath}.get_posts_by_avatar").return_value = mocked_posts
        mocker.patch(f"{AvatarsStoragePath}.get_by_user_id").return_value = get_fake_avatar(
            user_id=john_doe.user_id, avatar_id=avatar_id
        )
        response = await client.get("/api/posts/", headers=john_doe.headers_mixin)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == [
            json.loads(PostResponse.model_validate(post).model_dump_json()) for post in mocked_posts
        ]


class TestGetPostById:
    async def test_auth_required(self, client: AsyncClient):
        post_uuid = uuid4()
        response = await client.get(f"/api/posts/{post_uuid}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_post_not_found(self, client: AsyncClient, mocker: MockerFixture, john_doe):
        post_uuid = uuid4()
        mocker.patch(f"{PostStoragePath}.get_posts_by_avatar").return_value = []
        mocker.patch(f"{AvatarsStoragePath}.get_by_user_id").return_value = get_fake_avatar(
            user_id=john_doe.user_id, avatar_id=random.randint(1, 20)
        )
        response = await client.get(f"/api/posts/{post_uuid}", headers=john_doe.headers_mixin)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_post_by_id(self, client: AsyncClient, mocker: MockerFixture, john_doe):
        avatar_id = random.randint(1, 20)
        post_uuid = uuid4()
        mocked_post = Post(
            uuid=post_uuid,
            avatar_id=avatar_id,
            post_text="text",
            images=["link"],
            created_at=datetime.datetime.now(),
        )

        mocker.patch(f"{PostStoragePath}.get_posts_by_avatar").return_value = [mocked_post]
        mocker.patch(f"{AvatarsStoragePath}.get_by_user_id").return_value = get_fake_avatar(
            user_id=john_doe.user_id, avatar_id=avatar_id
        )
        response = await client.get(f"/api/posts/{post_uuid}", headers=john_doe.headers_mixin)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == json.loads(PostResponse.model_validate(mocked_post).model_dump_json())


class TestCreatePost:
    async def test_auth_required(self, client: AsyncClient):
        post_data = {"post_text": "Hello World", "images": ["image1.jpg"]}
        response = await client.post("/api/posts/", json=post_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_create_post(self, client: AsyncClient, mocker: MockerFixture, john_doe):
        avatar_id = random.randint(1, 20)
        post_data = {"post_text": "New post", "images": ["image1.jpg"]}
        new_post = Post(
            uuid=uuid4(),
            avatar_id=avatar_id,
            post_text=post_data["post_text"],
            images=post_data["images"],
            created_at=datetime.datetime.now(),
        )
        mocker.patch(f"{PostStoragePath}.create").return_value = new_post
        mocker.patch(f"{AvatarsStoragePath}.get_by_user_id").return_value = get_fake_avatar(
            user_id=john_doe.user_id, avatar_id=avatar_id
        )
        response = await client.post("/api/posts/", headers=john_doe.headers_mixin, json=post_data)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == json.loads(PostResponse.model_validate(new_post).model_dump_json())


class TestDeletePost:
    async def test_auth_required(self, client: AsyncClient):
        post_uuid = uuid4()
        response = await client.delete(f"/api/posts/{post_uuid}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_delete_non_existent_post(self, client: AsyncClient, mocker: MockerFixture, john_doe):
        post_uuid = uuid4()
        mocker.patch(f"{PostStoragePath}.delete_posts").return_value = None
        mocker.patch(f"{AvatarsStoragePath}.get_by_user_id").return_value = get_fake_avatar(
            user_id=john_doe.user_id, avatar_id=random.randint(1, 20)
        )

        response = await client.delete(f"/api/posts/{post_uuid}", headers=john_doe.headers_mixin)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_post(self, client: AsyncClient, mocker: MockerFixture, john_doe):
        avatar_id = random.randint(1, 20)
        post_uuid = uuid4()
        mocker.patch(f"{PostStoragePath}.delete_posts").return_value = post_uuid
        mocker.patch(f"{AvatarsStoragePath}.get_by_user_id").return_value = get_fake_avatar(
            user_id=john_doe.user_id, avatar_id=avatar_id
        )
        response = await client.delete(f"/api/posts/{post_uuid}", headers=john_doe.headers_mixin)
        assert response.status_code == status.HTTP_200_OK
        assert response.json().get("deleted_post_uuid") == str(post_uuid)


def get_fake_avatar(user_id, avatar_id):
    return Avatar(
        id=avatar_id,
        user_id=user_id,
    )
