import pytest

from core.eye_tracker import (
    EyeTracker, calculate_ear, STATE_OPEN, STATE_CLOSED, STATE_NO_FACE, STATE_INACTIVE,
)

OPEN_EYE = [(0, 0), (3, -2), (7, -2), (10, 0), (7, 2), (3, 2)]     # EAR = 0.4
CLOSED_EYE = [(0, 0), (3, -0.5), (7, -0.5), (10, 0), (7, 0.5), (3, 0.5)]  # EAR = 0.1


def test_ear_open_and_closed():
    assert calculate_ear(OPEN_EYE) == pytest.approx(0.4)
    assert calculate_ear(CLOSED_EYE) == pytest.approx(0.1)


@pytest.mark.parametrize("coords", [[], [(0, 0)] * 5, [(1, 1)] * 6])
def test_ear_degenerate_input_returns_zero(coords):
    assert calculate_ear(coords) == 0.0


@pytest.fixture
def tracker(clock):
    t = EyeTracker(ear_threshold=0.21, clock=clock)
    t.is_active = True
    t.reset_statistics()
    return t


def test_inactive_state_before_start(clock):
    assert EyeTracker(clock=clock).eye_state == STATE_INACTIVE


def test_closed_duration_is_measured_in_seconds(tracker, clock):
    tracker.update_state(0.30)
    tracker.update_state(0.10)
    assert tracker.eye_state == STATE_CLOSED
    clock.advance(1.5)
    tracker.update_state(0.10)          # peu importe le nombre d'images
    assert tracker.closed_seconds() == pytest.approx(1.5)
    tracker.update_state(0.30)
    assert tracker.eye_state == STATE_OPEN
    assert tracker.closed_seconds() == 0.0


def test_blink_counted_once_per_closure(tracker):
    assert not tracker.update_state(0.30)
    assert tracker.update_state(0.10)
    assert not tracker.update_state(0.10)
    tracker.update_state(0.30)
    assert tracker.update_state(0.10)
    assert tracker.blink_counter == 2


def test_face_lost_is_tracked_and_resets_closed_timer(tracker, clock):
    tracker.update_state(0.10)
    clock.advance(0.5)
    tracker.update_state(None)
    assert tracker.eye_state == STATE_NO_FACE
    assert tracker.closed_seconds() == 0.0
    clock.advance(3.0)
    tracker.update_state(None)
    assert tracker.face_missing_seconds() == pytest.approx(3.0)
    tracker.update_state(0.30)
    assert tracker.face_missing_seconds() == 0.0


def test_blink_rate_uses_elapsed_time(tracker, clock):
    tracker.update_state(0.30)
    tracker.update_state(0.10)
    tracker.update_state(0.30)
    clock.advance(30.0)
    assert tracker.get_statistics()['blink_rate'] == pytest.approx(2.0)
