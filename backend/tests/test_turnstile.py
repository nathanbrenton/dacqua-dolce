from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.turnstile import verify_public_form_turnstile


def req(token=None):
    return SimpleNamespace(headers={"X-Turnstile-Token": token} if token else {})


def settings(enabled=True):
    return SimpleNamespace(
        turnstile_enabled=enabled,
        turnstile_secret="not-a-real-secret",
        turnstile_expected_hostname="dacquadolce.com",
    )


def test_disabled():
    with patch("app.services.turnstile.get_settings", return_value=settings(False)):
        verify_public_form_turnstile(req(), action="support")


def test_missing_token_rejected():
    with patch("app.services.turnstile.get_settings", return_value=settings()):
        with pytest.raises(HTTPException) as error:
            verify_public_form_turnstile(req(), action="quote")
        assert error.value.status_code == 400


@pytest.mark.parametrize(
    "response,accepted",
    [
        ({"success": True, "hostname": "dacquadolce.com", "action": "quote"}, True),
        ({"success": False, "hostname": "dacquadolce.com", "action": "quote"}, False),
        ({"success": True, "hostname": "other.test", "action": "quote"}, False),
        ({"success": True, "hostname": "dacquadolce.com", "action": "support"}, False),
    ],
)
def test_siteverify_evidence(response, accepted):
    client = MagicMock()
    client.__enter__.return_value = client
    client.post.return_value.json.return_value = response
    with (
        patch("app.services.turnstile.get_settings", return_value=settings()),
        patch("app.services.turnstile.httpx.Client", return_value=client),
    ):
        if accepted:
            verify_public_form_turnstile(req("token"), action="quote")
        else:
            with pytest.raises(HTTPException) as error:
                verify_public_form_turnstile(req("token"), action="quote")
            assert error.value.status_code == 400
    assert client.post.call_count == 1
    assert client.post.call_args.kwargs["data"]["response"] == "token"
