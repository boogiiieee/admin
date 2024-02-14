from fastapi import status
from fastapi_mail import MessageSchema
from httpx import AsyncClient
from pytest_mock import MockerFixture

from publication_admin.auth.jwt import JWTManager
from publication_admin.db.models import EmailCode, User


class TestGetCode:
    EmailCodeIssuerPath = "publication_admin.api.routers.auth.EmailCodeIssuer"

    async def test_request_body_validation(self, client: AsyncClient, mocker: MockerFixture):
        for req_body in (
            {"email": "exampletest.com"},
            {"email": ""},
            {},
        ):
            response = await client.post("/api/auth/get-code/", json=req_body)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            body = response.json()
            assert body["error_code"] != ""
            assert body["message"] != ""
            assert body["details"] is not None

    async def test_rate_limit(self, client: AsyncClient, mocker: MockerFixture):
        mocker.patch(f"{self.EmailCodeIssuerPath}.is_sending_code_too_fast").return_value = True
        response = await client.post("/api/auth/get-code/", json={"email": "example@test.com"})

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    async def test_send_new_code(self, client: AsyncClient, mocker: MockerFixture, send_email_mock):
        user = "papa@mozhet.su"
        mocker.patch(f"{self.EmailCodeIssuerPath}.is_sending_code_too_fast").return_value = False
        mocker.patch(f"{self.EmailCodeIssuerPath}.create_new_code").return_value = EmailCode(email=user, code="123456")

        response = await client.post("/api/auth/get-code/", json={"email": user})

        message_to_send: MessageSchema = send_email_mock.call_args.args[0]
        assert message_to_send.recipients == [user], "Expected concrete recipient for the email code"
        assert message_to_send.subject, "Expected non empty subject for email"
        assert "123-456" in message_to_send.body, "Expected the code inside email"  # type: ignore[operator]
        assert response.status_code == status.HTTP_204_NO_CONTENT


class TestAuthenticate:
    EmailAuthenticatorPath = "publication_admin.api.routers.auth.EmailAuthenticator"

    async def test_request_body_validation(self, client: AsyncClient, mocker: MockerFixture):
        response = await client.post("/api/auth/authenticate/", json={"email": "example@test.com"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        response = await client.post("/api/auth/authenticate/", json={"code": "123456"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_authenticate_with_error(self, client: AsyncClient, mocker: MockerFixture):
        from publication_admin.auth.email_auth import AuthenticationError

        mocker.patch(f"{self.EmailAuthenticatorPath}.authenticate").side_effect = AuthenticationError("Test")
        response = await client.post("/api/auth/authenticate/", json={"email": "example@test.com", "code": "123123"})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        body = response.json()
        assert body["error_code"] == "auth.invalid_credentials"

    async def test_authenticate_sign_up(self, client: AsyncClient, mocker: MockerFixture, send_email_mock):
        from publication_admin.settings import settings

        mocker.patch(f"{self.EmailAuthenticatorPath}.authenticate").return_value = None
        mocker.patch(f"{self.EmailAuthenticatorPath}.get_user").return_value = None

        user = "papa@mozhet.su"
        register_user_mock = mocker.patch(f"{self.EmailAuthenticatorPath}.register_user")
        register_user_mock.return_value = User(id=1, email=user)

        response = await client.post("/api/auth/authenticate/", json={"email": user, "code": "123456"})

        assert response.status_code == status.HTTP_200_OK
        register_user_mock.assert_awaited_once()
        payload = JWTManager(secret_key=settings.secret_key).get_payload(response.json().get("access_token"))
        assert payload["user_id"] == 1, "Unmatched user_id in jwt payload"
        assert payload["email"] == user, "Unmatched email in jwt payload"
        assert payload["expiration"] > 0, "JWT must have expiration"

    async def test_authenticate_sign_in(self, client: AsyncClient, mocker: MockerFixture, send_email_mock):
        from publication_admin.settings import settings

        user = "papa@vsemozhet.su"
        mocker.patch(f"{self.EmailAuthenticatorPath}.authenticate").return_value = None
        mocker.patch(f"{self.EmailAuthenticatorPath}.get_user").return_value = User(id=14, email=user)

        response = await client.post("/api/auth/authenticate/", json={"email": user, "code": "666777"})

        assert response.status_code == status.HTTP_200_OK
        mocker.patch(f"{self.EmailAuthenticatorPath}.register_user").assert_not_awaited()

        payload = JWTManager(secret_key=settings.secret_key).get_payload(response.json().get("access_token"))
        assert payload["user_id"] == 14, "Unmatched user_id in jwt payload"
        assert payload["email"] == user, "Unmatched email in jwt payload"
        assert payload["expiration"] > 0, "JWT must have expiration"
