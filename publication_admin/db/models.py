import secrets
from enum import StrEnum
from string import ascii_letters

from sqlalchemy import JSON, TIMESTAMP, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func
from sqlalchemy.sql import text as sql_text

LORA_NAME_LENGTH = 11


class InitStatus(StrEnum):
    CREATED: str = "CREATED"
    PENDING: str = "PENDING"
    SUCCESS: str = "SUCCESS"


class BaseModel(DeclarativeBase):
    pass


class User(BaseModel):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True)


class EmailCode(BaseModel):
    __tablename__ = "email_codes"

    email = Column(String, primary_key=True)
    code = Column(String)
    attempts = Column(Integer, default=3)
    created_at = Column(DateTime, server_default=func.now())


class Avatar(BaseModel):
    __tablename__ = "avatars"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    images = Column(JSON)
    topics = Column(JSON)
    name = Column(String)
    text = Column(String)

    init_persona_task_id = Column(String, nullable=True, default=None)
    init_status = Column(Enum(InitStatus), default=InitStatus.CREATED, server_default=sql_text(InitStatus.CREATED))
    lora_path = Column(String, default="")
    profile_image = Column(String, default="")
    lora_name = Column(String, unique=True, nullable=True)

    def set_random_lora_name(self):
        self.lora_name = "".join(secrets.choice(ascii_letters) for _ in range(LORA_NAME_LENGTH))


class Topic(BaseModel):
    __tablename__ = "topics"

    name = Column(String, primary_key=True)


class Post(BaseModel):
    __tablename__ = "posts"

    uuid = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sql_text("uuid_generate_v4()"),
    )
    avatar_id = Column(Integer, ForeignKey("avatars.id", ondelete="CASCADE"))
    post_text = Column(Text, nullable=True, default="")
    images = Column(ARRAY(String), default=list)
    created_at = Column(TIMESTAMP(timezone=True), server_default=sql_text("now()"))
