import pytest

from app.core.launch_config import LaunchConfigurationError, load_launch_runtime_settings


def test_launch_phase_defaults_to_prelaunch() -> None:
    settings = load_launch_runtime_settings({})
    assert settings.phase == "prelaunch"
    assert settings.commerce_phase_enabled is False


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("prelaunch", "prelaunch"),
        ("SOFT_LAUNCH", "soft_launch"),
        (" public_launch ", "public_launch"),
    ],
)
def test_launch_phase_accepts_supported_values(value: str, expected: str) -> None:
    settings = load_launch_runtime_settings({"DACQUA_LAUNCH_PHASE": value})
    assert settings.phase == expected


def test_launch_phase_rejects_unknown_value() -> None:
    with pytest.raises(LaunchConfigurationError, match="DACQUA_LAUNCH_PHASE"):
        load_launch_runtime_settings({"DACQUA_LAUNCH_PHASE": "live"})
