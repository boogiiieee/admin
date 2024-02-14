from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TypedDict

import jwt

JWT_EXPIRES_DELTA = 3600 * 24 * 7


class JWTError(Exception):
    pass


class JWTPayload(TypedDict):
    user_id: int
    email: str
    expiration: int


@dataclass
class JWTManager:
    secret_key: str
    algorithm: str = "HS256"

    def create_access_token(self, *, email: str, user_id: int, expires_delta: int = JWT_EXPIRES_DELTA) -> str:
        if not email:
            raise JWTError("Empty email")

        if not user_id:
            raise JWTError("Empty user_id")

        expiration = int(datetime.now(UTC).timestamp()) + expires_delta
        payload: JWTPayload = {"user_id": user_id, "email": email, "expiration": expiration}
        encoded_jwt = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def get_payload(self, token: str) -> JWTPayload:
        try:
            payload: JWTPayload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except jwt.PyJWTError as exc:
            raise JWTError("Invalid token") from exc

        email = payload.get("email")
        user_id = payload.get("user_id")
        if not email or not user_id:
            raise JWTError(f"Invalid payload {payload}")

        expiration = payload.get("expiration")
        if not expiration or expiration < datetime.now(UTC).timestamp():
            raise JWTError(f"Token is expired: {expiration}")

        return payload

    def get_user_email(self, token: str) -> str:
        payload: JWTPayload = self.get_payload(token)
        return payload["email"]

    def get_user_id(self, token: str) -> int:
        payload: JWTPayload = self.get_payload(token)
        return payload["user_id"]
