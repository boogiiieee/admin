from unittest.mock import AsyncMock

from fastapi import status
from httpx import AsyncClient

from publication_admin.api.errors import ErrorCode
from publication_admin.db.models import User


class TestGetCurrentUser:
    "Test for get_current_user dependency"

    async def test_get_current_user_no_token(self, client: AsyncClient):
        response = await client.get("/api/users/me/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        response = await client.get("/api/users/me/", headers={"Authorization": "Bearer INVALID_JWT"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["error_code"] == ErrorCode.auth_unauthorized

    async def test_get_current_user_ok(self, client: AsyncClient, jwt_manager, session_mock):
        session_mock.get = AsyncMock(return_value=User(email="biba@boba.com", id=123))
        token = jwt_manager.create_access_token(email="biba@boba.com", user_id=123)
        response = await client.get("/api/users/me/", headers={"Authorization": f"Bearer {token}"})

        session_mock.get.assert_awaited_once_with(User, 123)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == 123
        assert response.json()["email"] == "biba@boba.com"

    async def test_get_current_user_deleted(self, client: AsyncClient, jwt_manager, session_mock):
        session_mock.get = AsyncMock(return_value=None)
        token = jwt_manager.create_access_token(email="biba@boba.com", user_id=321)
        response = await client.get("/api/users/me/", headers={"Authorization": f"Bearer {token}"})

        session_mock.get.assert_awaited_once_with(User, 321)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["error_code"] == ErrorCode.auth_unauthorized
