from abc import ABC, abstractmethod

from fastapi_mail import MessageSchema, MessageType

from publication_admin.auth.otp import format_otp
from publication_admin.db.models import EmailCode


class EmailMessage(ABC):
    """Email-message template renderer"""

    @abstractmethod
    def subject(self) -> str:
        """Subject content of the mail"""

    @abstractmethod
    async def html_body(self) -> str:
        """Body of the message"""

    async def render(self) -> MessageSchema:
        return MessageSchema(
            subject=self.subject(),
            recipients=[],
            body=await self.html_body(),
            subtype=MessageType.html,
        )


class EmailCodeIssueMessage(EmailMessage):
    """
    Authorization email with One-Time-Password
    """

    def __init__(self, email_code: EmailCode) -> None:
        self.email_code = email_code

    def subject(self):
        return "publication_admin authorization"

    async def html_body(self):
        return f"""
                <h1>Authorization</h1>
                <p>Your one-time-password: <b>{format_otp(str(self.email_code.code))}</b></p>
            """
