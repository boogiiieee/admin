from datetime import datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from publication_admin.auth.email_messages import EmailCodeIssueMessage
from publication_admin.auth.otp import generate_otp
from publication_admin.auth.utils import normalize_email
from publication_admin.db.models import EmailCode, User
from publication_admin.settings import settings

OTP_TTL = timedelta(minutes=5)
OTP_SEND_THROTTLE = timedelta(seconds=30)


class EmailCodeIssuer:
    def __init__(self, email: str, session: AsyncSession):
        self.session = session
        self.email = normalize_email(email)

    async def is_sending_code_too_fast(self) -> bool:
        prev_code = await self.session.get(EmailCode, self.email)

        if prev_code:
            time_elapsed_since_prev_code = datetime.utcnow() - prev_code.created_at

            if time_elapsed_since_prev_code < OTP_SEND_THROTTLE and settings.enable_email_code_rate_limit:
                return True

        return False

    async def create_new_code(self) -> EmailCode:
        otp = generate_otp()

        await self.session.execute(delete(EmailCode).where(EmailCode.email == self.email))
        email_code = EmailCode(email=self.email, code=otp)
        self.session.add(email_code)
        await self.session.commit()
        await self.session.refresh(email_code)

        return email_code

    async def get_email_message(self, email_code: EmailCode):
        message = await EmailCodeIssueMessage(email_code).render()
        message.recipients.append(str(email_code.email))
        return message


class AuthenticationError(Exception):
    pass


class EmailAuthenticator:
    def __init__(self, email: str, session: AsyncSession):
        self.session = session
        self.email = normalize_email(email)

    async def authenticate(self, code: str) -> None:
        db_code = await self.session.get(EmailCode, self.email)

        if db_code is None:
            raise AuthenticationError("Invalid code")

        if db_code.attempts < 1:
            raise AuthenticationError("Too many attempts")
        if db_code.created_at + OTP_TTL < datetime.utcnow():
            raise AuthenticationError("Code already expired")
        if db_code.code != code:
            db_code.attempts -= 1
            await self.session.commit()
            raise AuthenticationError("Invalid code")

        await self.session.delete(db_code)
        await self.session.commit()

    async def get_user(self) -> User | None:
        user = (await self.session.execute(select(User).where(User.email == self.email))).scalar()
        return user

    async def register_user(self) -> User:
        user = User(email=self.email)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
