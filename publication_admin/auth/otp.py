import secrets
import string

OTP_LENGTH = 6


def generate_otp() -> str:
    return "".join(secrets.choice(string.digits) for _ in range(OTP_LENGTH))


def format_otp(otp: str) -> str:
    middle = OTP_LENGTH // 2
    return otp[:middle] + "-" + otp[middle:]
