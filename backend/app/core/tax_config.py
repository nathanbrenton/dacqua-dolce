from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass


class TaxConfigurationError(ValueError):
    pass


@dataclass(frozen=True)
class TaxRuntimeSettings:
    mode: str
    stripe_secret_key: str | None

    @property
    def enabled(self) -> bool:
        return self.mode == "stripe_test"


def load_tax_runtime_settings(
    environ: Mapping[str, str] | None = None,
) -> TaxRuntimeSettings:
    source = os.environ if environ is None else environ
    mode = source.get("DACQUA_TAX_PROVIDER", "disabled").strip().lower()

    if mode not in {"disabled", "stripe_test"}:
        raise TaxConfigurationError(
            "DACQUA_TAX_PROVIDER must be disabled or stripe_test. "
            "PT44 intentionally does not support live tax credentials."
        )

    secret_key = source.get("STRIPE_TAX_SECRET_KEY")
    if secret_key is not None:
        secret_key = secret_key.strip() or None

    if mode == "stripe_test":
        if secret_key is None:
            raise TaxConfigurationError(
                "STRIPE_TAX_SECRET_KEY is required for stripe_test."
            )
        if not secret_key.startswith(("sk_test_", "rk_test_")):
            raise TaxConfigurationError(
                "PT44 accepts Stripe test-mode credentials only."
            )

    return TaxRuntimeSettings(
        mode=mode,
        stripe_secret_key=secret_key,
    )
