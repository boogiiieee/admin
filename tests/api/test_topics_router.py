from fastapi import status
from httpx import AsyncClient
from pytest_mock import MockerFixture

from publication_admin.db.models import Topic

TopicsStoragePath = "publication_admin.api.routers.topics.TopicsStorage"


class TestGetAll:
    async def test_auth_required(self, client: AsyncClient):
        response = await client.get("/api/topics/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_all(self, client: AsyncClient, mocker: MockerFixture, john_doe):
        mocker.patch(f"{TopicsStoragePath}.all").return_value = [
            Topic(name="pet"),
            Topic(name="food"),
            Topic(name="alco"),
        ]
        response = await client.get("/api/topics/", headers=john_doe.headers_mixin)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == [{"name": "pet"}, {"name": "food"}, {"name": "alco"}]
