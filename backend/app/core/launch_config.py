from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from os import environ
from typing import Literal, cast

LaunchPhase = Literal["prelaunch", "soft_launch", "public_launch"]


class LaunchConfigurationError(ValueError):
    pass


@dataclass(frozen=True)
class LaunchRuntimeSettings:
    phase: LaunchPhase

    @property
    def commerce_phase_enabled(self) -> bool:
        return self.phase == "public_launch"


def load_launch_runtime_settings(
    environment: Mapping[str, str] | None = None,
) -> LaunchRuntimeSettings:
    source = environ if environment is None else environment
    raw_phase = source.get("DACQUA_LAUNCH_PHASE", "prelaunch").strip().lower()

    if raw_phase not in {"prelaunch", "soft_launch", "public_launch"}:
        raise LaunchConfigurationError(
            "DACQUA_LAUNCH_PHASE must be prelaunch, soft_launch, or public_launch."
        )

    return LaunchRuntimeSettings(
        phase=cast(LaunchPhase, raw_phase),
    )
