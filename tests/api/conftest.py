from unittest.mock import Mock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def app(app_session, send_email_mock, session_mock, media_storage_mock):
    # Stub deps with mocks before each app usage
    from publication_admin.api.deps import get_db, media_storage, send_email

    app_session.dependency_overrides[get_db] = lambda: session_mock
    app_session.dependency_overrides[send_email] = lambda: send_email_mock
    app_session.dependency_overrides[media_storage] = lambda: media_storage_mock

    return app_session


@pytest.fixture
def send_email_mock():
    return Mock(name="send_email_mock")


@pytest.fixture
def session_mock():
    return Mock(name="db_session_mock", spec_set=AsyncSession)


@pytest.fixture
def media_storage_mock():
    from publication_admin.media_storage.s3 import S3MediaStorage

    return Mock(name="media_storage_mock", spec_set=S3MediaStorage)


@pytest.fixture
async def client(app):
    async with AsyncClient(app=app, base_url="http://127.0.0.1:8000/") as client:
        yield client
