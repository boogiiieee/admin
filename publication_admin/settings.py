from enum import StrEnum

from fastapi_mail import ConnectionConfig
from loguru import logger
from pydantic_core import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Env(StrEnum):
    LOCAL: str = "local"
    DEV: str = "dev"
    TEST: str = "test"
    PROD: str = "prod"


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_host: str
    postgres_port: int

    @property
    def db_connection(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


class MediaStorageSettings(BaseSettings):
    media_storage_url: str
    media_storage_access_key_id: str
    media_storage_secret_access_key: str
    media_storage_bucket: str
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class MailConnectionConfig(ConnectionConfig):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    env: Env = Env.LOCAL
    secret_key: str
    enable_email_code_rate_limit: bool = True
    image_size_limit: int = 10 * 1024 * 1024

    ml_text_service_url: str
    ml_images_service_url: str
    media_storage: MediaStorageSettings
    database: DatabaseSettings
    mail: MailConnectionConfig

    def is_local_env(self):
        return self.env == Env.LOCAL


try:
    settings = Settings(
        media_storage=MediaStorageSettings(),
        database=DatabaseSettings(),
        mail=MailConnectionConfig(
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True,
        ),
    )
except ValidationError as e:
    logger.critical("Some environment variables are missing or invalid!")

    for env_error in e.errors():
        env_name = env_error["loc"][0]
        logger.critical(f"{env_name}: {env_error['msg']}")

    raise e
