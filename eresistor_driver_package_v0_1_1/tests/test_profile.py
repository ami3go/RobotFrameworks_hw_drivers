from eresistor_driver.models import DeviceProfile, ConnectionLossPolicy
from eresistor_driver.profile import profile_from_dict, profile_to_dict


def test_profile_roundtrip_dict():
    profile = profile_from_dict({
        "host": "192.168.7.50",
        "safety": {"connection_loss_policy": "attempt_all_off"},
        "watchdog": {"enabled": True, "keepalive_interval_s": 10},
    })
    assert profile.host == "192.168.7.50"
    assert profile.safety.connection_loss_policy == ConnectionLossPolicy.ATTEMPT_ALL_OFF
    assert profile.watchdog.enabled is True
    data = profile_to_dict(profile)
    assert data["safety"]["connection_loss_policy"] == "attempt_all_off"
