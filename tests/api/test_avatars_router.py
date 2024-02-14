from fastapi import status
from httpx import AsyncClient
from pytest_mock import MockerFixture

from publication_admin.db.models import Avatar

AvatarsStoragePath = "publication_admin.api.routers.avatars.AvatarsStorage"
TopicsStoragePath = "publication_admin.api.routers.avatars.TopicsStorage"


class TestGetCurrentAvatar:
    async def test_auth_required(self, client: AsyncClient):
        response = await client.get("/api/avatars/current/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_no_avatars(self, client: AsyncClient, mocker: MockerFixture, john_doe):
        mocker.patch(f"{AvatarsStoragePath}.get_by_user_id").return_value = None
        response = await client.get("/api/avatars/current/", headers=john_doe.headers_mixin)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_return_avatar(self, client: AsyncClient, mocker: MockerFixture, john_doe):
        mocker.patch(f"{AvatarsStoragePath}.get_by_user_id").return_value = faky_avatar(john_doe.user_id)

        response = await client.get("/api/avatars/current/", headers=john_doe.headers_mixin)
        assert response.status_code == status.HTTP_200_OK
        assert_faky_avatar_response(response.json())


class TestCreateAvatar:
    valid_payload = {"name": "test", "text": "test", "topics": [], "images": []}

    async def test_request_body_validation(self, client: AsyncClient, john_doe):
        response = await client.post("/api/avatars/", json={}, headers=john_doe.headers_mixin)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_auth_required(self, client: AsyncClient):
        response = await client.post("/api/avatars/", json=self.valid_payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_already_have_avatars(self, client: AsyncClient, mocker: MockerFixture, john_doe):
        mocker.patch(f"{AvatarsStoragePath}.exists_for_user").return_value = True
        response = await client.post("/api/avatars/", json=self.valid_payload, headers=john_doe.headers_mixin)
        assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED

    async def test_created(self, client: AsyncClient, mocker: MockerFixture, john_doe):
        mocker.patch(f"{AvatarsStoragePath}.exists_for_user").return_value = False
        create_mock = mocker.patch(f"{AvatarsStoragePath}.create")
        create_mock.return_value = faky_avatar(john_doe.user_id)

        response = await client.post("/api/avatars/", json=self.valid_payload, headers=john_doe.headers_mixin)
        assert response.status_code == status.HTTP_200_OK

        create_mock.assert_awaited_once()
        create_mock.call_args_list[0].kwargs["user_id"] = john_doe.user_id
        assert_faky_avatar_response(response.json())


class TestPatchAvatar:
    valid_payload = {"name": "test_patch", "text": "test_patch", "topics": [" patching ", "debug"]}

    async def test_request_body_validation(self, client: AsyncClient, john_doe):
        response = await client.patch("/api/avatars/current/", json={}, headers=john_doe.headers_mixin)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_auth_required(self, client: AsyncClient):
        response = await client.patch("/api/avatars/current/", json=self.valid_payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_no_avatars(self, client: AsyncClient, mocker: MockerFixture, john_doe):
        mocker.patch(f"{AvatarsStoragePath}.get_by_user_id").return_value = None
        response = await client.patch("/api/avatars/current/", json=self.valid_payload, headers=john_doe.headers_mixin)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_patched(self, client: AsyncClient, mocker: MockerFixture, john_doe):
        mocker.patch(f"{AvatarsStoragePath}.get_by_user_id").return_value = faky_avatar(user_id=john_doe.user_id)
        add_new_topics_mock = mocker.patch(f"{TopicsStoragePath}.add_new_topics")
        response = await client.patch("/api/avatars/current/", json=self.valid_payload, headers=john_doe.headers_mixin)

        assert response.status_code == status.HTTP_200_OK
        add_new_topics_mock.assert_awaited_once_with(["patching", "debug"])
        body = response.json()
        assert body["name"] == "test_patch"
        assert body["text"] == "test_patch"
        assert body["topics"] == ["patching", "debug"]
        assert body["images"] is not None

    async def test_delete(self, client: AsyncClient, mocker: MockerFixture, john_doe):
        mocker.patch(f"{AvatarsStoragePath}.get_by_user_id").return_value = faky_avatar(user_id=john_doe.user_id)
        mocker.patch(f"{AvatarsStoragePath}.delete_avatar").return_value = 1
        response = await client.delete("/api/avatars/current/", headers=john_doe.headers_mixin)
        assert response.status_code == status.HTTP_200_OK

    async def test_delete_404(self, client: AsyncClient, mocker: MockerFixture, john_doe):
        mocker.patch(f"{AvatarsStoragePath}.get_by_user_id").return_value = None
        response = await client.delete("/api/avatars/current/", headers=john_doe.headers_mixin)
        assert response.status_code == status.HTTP_404_NOT_FOUND


def faky_avatar(user_id):
    return Avatar(
        id=1,
        user_id=user_id,
        name="John",
        text="I am blue humanoid",
        topics=["food", "pets"],
        images=["secret_image_of_me.jpg"],
    )


def assert_faky_avatar_response(body: dict):
    assert body["name"] == "John"
    assert body["text"] == "I am blue humanoid"
    assert body["topics"] == ["food", "pets"]
    assert body["images"] == ["secret_image_of_me.jpg"]
