from dataclasses import dataclass

import pytest


@pytest.fixture(scope="session")
def app_session():
    from publication_admin.main import app

    return app


@pytest.fixture
def jwt_manager():
    from publication_admin.auth.jwt import JWTManager

    return JWTManager("test")


@dataclass
class DummyPerson:
    email: str
    user_id: int
    headers_mixin: dict


@pytest.fixture
def john_doe(jwt_manager) -> DummyPerson:
    token = jwt_manager.create_access_token(email="john_doe@mail.com", user_id=666)
    headers_mixin = {"Authorization": f"Bearer {token}"}
    return DummyPerson(email="john_doe@mail.com", user_id=666, headers_mixin=headers_mixin)
