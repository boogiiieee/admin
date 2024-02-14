def normalize_email(email: str) -> str:
    # TODO: handle things like foo.b+ar@gmail.com  # noqa: TD002, TD003
    return email.lower()
