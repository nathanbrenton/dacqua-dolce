import pytest

from app.services.launch_gate import (
    CommerceLaunchGateError,
    assess_commerce_launch_gate,
    require_commerce_phase_allows_checkout,
)


@pytest.mark.parametrize("phase", ["prelaunch", "soft_launch"])
def test_nonpublic_launch_phases_keep_checkout_closed(phase) -> None:
    assessment = assess_commerce_launch_gate(phase=phase)
    assert assessment.checkout_phase_enabled is False

    with pytest.raises(CommerceLaunchGateError, match="public_launch"):
        require_commerce_phase_allows_checkout(phase=phase)


def test_public_launch_phase_only_opens_phase_gate() -> None:
    assessment = require_commerce_phase_allows_checkout(phase="public_launch")

    assert assessment.checkout_phase_enabled is True
    assert assessment.phase == "public_launch"
    assert "independent tax" in assessment.detail
