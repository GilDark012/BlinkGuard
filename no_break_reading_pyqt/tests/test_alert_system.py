import numpy as np
import pytest

from core.alert_system import AlertSystem, REASON_EYES_CLOSED, REASON_FACE_LOST


@pytest.fixture
def alerts(clock):
    return AlertSystem(trigger_seconds=1.0, duration=3.0, cooldown=10.0, reset_after=5.0,
                       face_lost_seconds=5.0, clock=clock, audio=False)


def test_no_alert_before_trigger(alerts):
    assert not alerts.check_and_trigger(0.9)
    assert alerts.get_alert_count() == 0


def test_first_alert_is_100_percent(alerts):
    assert alerts.check_and_trigger(1.0)
    assert alerts.last_reason == REASON_EYES_CLOSED
    assert alerts.get_alert_intensity() == pytest.approx(1.0)


def test_waits_duration_plus_cooldown_before_repeating(alerts, clock):
    assert alerts.check_and_trigger(1.0)
    clock.advance(12.9)
    assert not alerts.check_and_trigger(13.9)
    assert alerts.get_cooldown_remaining() == pytest.approx(0.1)
    clock.advance(0.1)
    assert alerts.check_and_trigger(14.0)
    assert alerts.get_alert_intensity() == pytest.approx(1.2)


def test_brief_eye_opening_does_not_bypass_cooldown(alerts, clock):
    assert alerts.check_and_trigger(1.0)
    clock.advance(2.0)
    assert not alerts.check_and_trigger(0.0)   # yeux ouverts une image
    clock.advance(1.0)
    assert not alerts.check_and_trigger(1.0)   # refermés : toujours en attente
    assert alerts.get_alert_count() == 1


def test_intensity_escalates_and_is_capped(alerts, clock):
    alerts.max_volume_multiplier = 1.5
    expected = [1.0, 1.2, 1.4, 1.5, 1.5]
    for value in expected:
        assert alerts.check_and_trigger(5.0)
        assert alerts.get_alert_intensity() == pytest.approx(value)
        clock.advance(13.0)


def test_intensity_resets_after_eyes_open_long_enough(alerts, clock):
    alerts.check_and_trigger(1.0)
    clock.advance(13.0)
    alerts.check_and_trigger(1.0)
    assert alerts.get_alert_count() == 2

    alerts.check_and_trigger(0.0)
    clock.advance(4.9)
    alerts.check_and_trigger(0.0)
    assert alerts.get_alert_count() == 2       # pas encore
    clock.advance(0.2)
    alerts.check_and_trigger(0.0)
    assert alerts.get_alert_count() == 0
    assert alerts.get_alert_intensity() == pytest.approx(1.0)


def test_face_lost_triggers_alert(alerts):
    assert not alerts.check_and_trigger(0.0, face_missing_seconds=4.9)
    assert alerts.check_and_trigger(0.0, face_missing_seconds=5.0)
    assert alerts.last_reason == REASON_FACE_LOST


def test_face_lost_alert_can_be_disabled(alerts):
    alerts.face_lost_alert = False
    assert not alerts.check_and_trigger(0.0, face_missing_seconds=60.0)


def test_alert_still_reported_when_sound_disabled(alerts):
    alerts.disable_sound()
    assert alerts.check_and_trigger(2.0)


def test_reset_clears_state(alerts):
    alerts.check_and_trigger(2.0)
    alerts.reset()
    assert alerts.get_cooldown_remaining() == 0.0
    assert alerts.check_and_trigger(2.0)


def test_wave_shape_and_range(alerts):
    alerts.volume_multiplier = 3.0
    wave = alerts.build_wave(duration=0.5, frequency=800, sample_rate=8000)
    assert wave.shape == (4000, 2)
    assert wave.dtype == np.int16
    assert np.abs(wave.astype(np.int32)).max() <= 32767
    assert wave.flags['C_CONTIGUOUS']
