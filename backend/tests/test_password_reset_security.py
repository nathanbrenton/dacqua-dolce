from app.services.password_reset import (
    generate_reset_token,
    hash_reset_token,
)


def test_reset_token_is_random_and_not_stored_raw() -> None:
    first = generate_reset_token()
    second = generate_reset_token()

    assert first != second
    assert len(first) >= 32
    assert len(second) >= 32

    first_hash = hash_reset_token(first)

    assert first_hash != first
    assert len(first_hash) == 64


def test_same_reset_token_hashes_deterministically() -> None:
    token = generate_reset_token()

    assert hash_reset_token(token) == hash_reset_token(token)
