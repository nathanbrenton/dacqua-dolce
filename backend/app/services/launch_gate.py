from __future__ import annotations

from dataclasses import dataclass

from app.core.launch_config import (
    LaunchConfigurationError,
    LaunchPhase,
    load_launch_runtime_settings,
)


class CommerceLaunchGateError(ValueError):
    pass


@dataclass(frozen=True)
class CommerceLaunchGateAssessment:
    phase: LaunchPhase
    checkout_phase_enabled: bool
    label: str
    detail: str


_PHASE_LABELS: dict[LaunchPhase, str] = {
    "prelaunch": "Prelaunch",
    "soft_launch": "Invited/test soft launch",
    "public_launch": "Public launch",
}


def assess_commerce_launch_gate(
    *,
    phase: LaunchPhase | None = None,
) -> CommerceLaunchGateAssessment:
    resolved_phase = (
        load_launch_runtime_settings().phase
        if phase is None
        else phase
    )

    if resolved_phase == "public_launch":
        return CommerceLaunchGateAssessment(
            phase=resolved_phase,
            checkout_phase_enabled=True,
            label=_PHASE_LABELS[resolved_phase],
            detail=(
                "The explicit public-launch phase permits checkout to continue "
                "to the independent tax, payment-provider, sales-area, and "
                "order-readiness guards."
            ),
        )

    if resolved_phase == "soft_launch":
        return CommerceLaunchGateAssessment(
            phase=resolved_phase,
            checkout_phase_enabled=False,
            label=_PHASE_LABELS[resolved_phase],
            detail=(
                "Invited/test soft launch keeps transactional checkout closed. "
                "Account, inquiry, quote, support, and operational validation "
                "workflows may continue without bypassing commerce blockers."
            ),
        )

    return CommerceLaunchGateAssessment(
        phase=resolved_phase,
        checkout_phase_enabled=False,
        label=_PHASE_LABELS[resolved_phase],
        detail=(
            "Prelaunch keeps transactional checkout closed while launch "
            "dependencies are commissioned."
        ),
    )


def require_commerce_phase_allows_checkout(
    *,
    phase: LaunchPhase | None = None,
) -> CommerceLaunchGateAssessment:
    try:
        assessment = assess_commerce_launch_gate(phase=phase)
    except LaunchConfigurationError as exc:
        raise CommerceLaunchGateError(
            "Commerce checkout is closed because launch configuration is invalid."
        ) from exc

    if assessment.checkout_phase_enabled:
        return assessment

    raise CommerceLaunchGateError(
        "Commerce checkout is closed for the current launch phase "
        f"({assessment.label}). Move to public_launch explicitly after all "
        "required commerce dependencies are commissioned."
    )
