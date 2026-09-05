from pwdlib import PasswordHash

# pwdlib's recommended configuration currently selects Argon2.
_password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Return a one-way password hash suitable for persistence."""

    if len(password) < 12:
        raise ValueError("Password must contain at least 12 characters.")

    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a candidate password against a stored password hash."""

    return _password_hash.verify(password, password_hash)
