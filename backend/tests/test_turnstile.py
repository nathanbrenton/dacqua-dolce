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


def test_production_requires_token_even_if_toggle_disabled():
    production = settings(False)
    production.is_production = True
    with patch("app.services.turnstile.get_settings", return_value=production):
        with pytest.raises(HTTPException) as error:
            verify_public_form_turnstile(req(), action="quote")
    assert error.value.status_code == 400


def test_production_requires_secret_even_if_toggle_disabled():
    production = settings(False)
    production.is_production = True
    production.turnstile_secret = None
    with patch("app.services.turnstile.get_settings", return_value=production):
        with pytest.raises(HTTPException) as error:
            verify_public_form_turnstile(req("token"), action="quote")
    assert error.value.status_code == 503


def test_production_disabled_toggle_still_validates_cloudflare():
    production = settings(False)
    production.is_production = True
    client = MagicMock()
    client.__enter__.return_value = client
    client.post.return_value.json.return_value = {
        "success": True,
        "hostname": production.turnstile_expected_hostname,
        "action": "quote",
    }
    with (
        patch("app.services.turnstile.get_settings", return_value=production),
        patch("app.services.turnstile.httpx.Client", return_value=client),
    ):
        verify_public_form_turnstile(req("token"), action="quote")
    assert client.post.call_count == 1


def test_development_disabled_toggle_still_skips_verification():
    development = settings(False)
    development.is_production = False
    with (
        patch("app.services.turnstile.get_settings", return_value=development),
        patch("app.services.turnstile.httpx.Client") as client,
    ):
        verify_public_form_turnstile(req(), action="quote")
    client.assert_not_called()
