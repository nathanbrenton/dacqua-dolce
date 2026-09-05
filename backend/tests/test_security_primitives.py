from app.services.passwords import hash_password, verify_password
from app.services.sessions import generate_session_token, hash_session_token


def test_password_is_stored_as_one_way_hash() -> None:
    password = "correct-horse-battery-staple"

    password_hash = hash_password(password)

    assert password_hash != password
    assert verify_password(password, password_hash)
    assert not verify_password("incorrect-password", password_hash)


def test_session_token_hash_is_stable_and_not_plaintext() -> None:
    token = generate_session_token()

    token_hash = hash_session_token(token)

    assert token_hash != token
    assert len(token_hash) == 64
    assert hash_session_token(token) == token_hash


def test_session_tokens_are_random() -> None:
    assert generate_session_token() != generate_session_token()
