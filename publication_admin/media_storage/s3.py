from typing import BinaryIO

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from loguru import logger

from publication_admin.settings import settings


class MediaStorageError(Exception):
    pass


class UploadError(MediaStorageError):
    pass


class S3MediaStorage:
    def __init__(self):
        self.client = boto3.client(
            service_name="s3",
            endpoint_url=settings.media_storage.media_storage_url,
            aws_access_key_id=settings.media_storage.media_storage_access_key_id,
            aws_secret_access_key=settings.media_storage.media_storage_secret_access_key,
            config=Config(signature_version="s3v4"),
        )

    def upload_file(self, filename: str, content: BinaryIO) -> None:
        try:
            self.client.put_object(
                Body=content,
                Bucket=settings.media_storage.media_storage_bucket,
                Key=filename,
            )
        except ClientError as e:
            logger.exception(e)
            raise UploadError(str(e)) from e
