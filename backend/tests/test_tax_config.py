import pytest

from app.core.tax_config import TaxConfigurationError, load_tax_runtime_settings


def test_tax_config_defaults_to_disabled() -> None:
    settings = load_tax_runtime_settings({})
    assert settings.mode == "disabled"
    assert settings.enabled is False
    assert settings.stripe_secret_key is None


def test_tax_config_requires_test_credential_for_stripe_test() -> None:
    with pytest.raises(TaxConfigurationError, match="STRIPE_TAX_SECRET_KEY"):
        load_tax_runtime_settings({"DACQUA_TAX_PROVIDER": "stripe_test"})


def test_tax_config_accepts_stripe_test_key() -> None:
    settings = load_tax_runtime_settings(
        {
            "DACQUA_TAX_PROVIDER": "stripe_test",
            "STRIPE_TAX_SECRET_KEY": "sk_test_example",
        }
    )
    assert settings.enabled is True
    assert settings.stripe_secret_key == "sk_test_example"


def test_tax_config_rejects_live_key() -> None:
    with pytest.raises(TaxConfigurationError, match="test-mode"):
        load_tax_runtime_settings(
            {
                "DACQUA_TAX_PROVIDER": "stripe_test",
                "STRIPE_TAX_SECRET_KEY": "sk_live_never_accept",
            }
        )


def test_tax_config_rejects_live_provider_mode() -> None:
    with pytest.raises(TaxConfigurationError, match="disabled or stripe_test"):
        load_tax_runtime_settings({"DACQUA_TAX_PROVIDER": "stripe_live"})
