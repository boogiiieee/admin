from fastapi import status
from httpx import AsyncClient


class TestUpload:
    jpeg_file = {"file": ("test.jpg", b"image data", "image/jpeg")}
    png_file = {"file": ("test.png", b"image data", "image/png")}
    jumbo_file = {"file": ("big_boy.jpeg", b"x" * 15 * 1024 * 1024, "image/jpeg")}

    async def test_require_auth(self, client: AsyncClient):
        response = await client.post("/api/files/image/upload/", data={}, files=self.jpeg_file)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_validation_jpeg(self, client: AsyncClient, john_doe):
        response = await client.post("/api/files/image/upload/", files=self.png_file, headers=john_doe.headers_mixin)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_validation_size(self, client: AsyncClient, john_doe):
        response = await client.post("/api/files/image/upload/", files=self.jumbo_file, headers=john_doe.headers_mixin)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_successful_upload(self, client: AsyncClient, media_storage_mock, john_doe):
        response = await client.post("/api/files/image/upload/", files=self.jpeg_file, headers=john_doe.headers_mixin)
        assert response.status_code == status.HTTP_200_OK
        media_storage_mock.upload_file.assert_called_once()
        assert response.json()["file_id"] != ""
        assert response.json()["url"] != ""
