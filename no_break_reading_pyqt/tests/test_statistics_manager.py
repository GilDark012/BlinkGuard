import csv
import json

import pytest

from core.statistics_manager import StatisticsManager


@pytest.fixture
def stats(clock):
    s = StatisticsManager(clock=clock)
    s.update_eye_tracking({'avg_ear': 0.12345, 'total_blinks': 4}, eye_state='FERME')
    s.update_reading({'current_page': 2, 'pages_read': 2})
    s.update_alert(True, 'eyes_closed')
    s.add_data_point()
    return s


def test_data_point_records_real_eye_state(stats):
    point = stats.data_points[0]
    assert point['eye_state'] == 'FERME'
    assert point['ear_avg'] == 0.1235
    assert point['alerts_count'] == 1


def test_csv_export_round_trip(stats, tmp_path):
    path = tmp_path / "s.csv"
    stats.export_to_csv(path)
    rows = list(csv.DictReader(path.open(encoding='utf-8')))
    assert rows[0]['eye_state'] == 'FERME'
    assert rows[0]['current_page'] == '2'


def test_csv_export_empty_still_has_header(clock, tmp_path):
    path = tmp_path / "empty.csv"
    StatisticsManager(clock=clock).export_to_csv(path)
    assert path.read_text(encoding='utf-8').startswith('timestamp,')


def test_json_export(stats, tmp_path, clock):
    clock.advance(3600)
    path = tmp_path / "s.json"
    stats.export_to_json(path)
    data = json.loads(path.read_text(encoding='utf-8'))
    assert data['summary']['total_alerts'] == 1
    assert data['summary']['reading_speed'] == pytest.approx(2.0)
    assert data['alerts']['alert_reasons'] == ['eyes_closed']


def test_export_failure_raises(stats, tmp_path):
    with pytest.raises(OSError):
        stats.export_to_csv(tmp_path / "missing_dir" / "s.csv")
