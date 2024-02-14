import re

from publication_admin.auth.otp import format_otp, generate_otp


def test_generate_otp():
    assert re.fullmatch(r"^\d{6}$", generate_otp()), "Auth OTP must be 6-digits string"


def test_format_otp():
    assert format_otp("666777") == "666-777"
