from datetime import UTC, datetime

import pytest

from publication_admin.auth.jwt import JWTError, JWTManager


def test_jwt_create_and_parse():
    jwter = JWTManager(secret_key="abc")
    now = int(datetime.now(UTC).timestamp())
    token = jwter.create_access_token(email="mishka@barni.com", user_id=12, expires_delta=666)

    assert token
    payload = jwter.get_payload(token)

    assert (
        payload["expiration"] >= now + 666 and payload["expiration"] < now + 670
    ), "JWT must be guaranteed to expire in specific time"

    user_id = jwter.get_user_id(token)
    email = jwter.get_user_email(token)

    assert user_id == payload["user_id"] == 12, "JWT payload must be consistent"
    assert email == payload["email"] == "mishka@barni.com", "JWT payload must be consistent"


def test_jwt_expiration():
    jwter = JWTManager(secret_key="abc")
    token = jwter.create_access_token(email="mishka@barni.com", user_id=12, expires_delta=0)

    with pytest.raises(JWTError, match=r"Token is expired"):
        jwter.get_payload(token)


def test_jwt_payload_format():
    jwter = JWTManager(secret_key="abc")

    with pytest.raises(JWTError, match=r"Empty .+"):
        jwter.create_access_token(email="test", user_id=None)

    with pytest.raises(JWTError, match=r"Empty .+"):
        jwter.create_access_token(email=None, user_id=123)
