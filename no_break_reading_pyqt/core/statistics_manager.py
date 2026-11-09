"""Module de gestion des statistiques"""
import csv
import json
import time
from datetime import datetime


class StatisticsManager:
    def __init__(self, clock=time.time):
        self._clock = clock
        self.reset()

    def reset(self):
        self.session_start_time = self._clock()
        self.eye_tracking_stats = {}
        self.reading_stats = {}
        self.last_eye_state = None
        self.alert_stats = {'total_alerts': 0, 'alert_times': [], 'alert_reasons': []}
        self.data_points = []

    def update_eye_tracking(self, eye_stats, eye_state=None):
        self.eye_tracking_stats = dict(eye_stats)
        if eye_state is not None:
            self.last_eye_state = eye_state

    def update_reading(self, pdf_data):
        self.reading_stats = dict(pdf_data)

    def update_alert(self, alert_triggered, reason=None):
        if alert_triggered:
            self.alert_stats['total_alerts'] += 1
            self.alert_stats['alert_times'].append(self._clock())
            self.alert_stats['alert_reasons'].append(reason)

    def add_data_point(self):
        """Enregistre l'état courant (à appeler uniquement pendant le tracking)."""
        self.data_points.append({
            'timestamp': datetime.fromtimestamp(self._clock()).isoformat(timespec='seconds'),
            'ear_avg': round(self.eye_tracking_stats.get('avg_ear', 0.0), 4),
            'eye_state': self.last_eye_state or '',
            'current_page': self.reading_stats.get('current_page', 0),
            'alerts_count': self.alert_stats['total_alerts'],
        })

    def get_summary(self):
        session_duration = self._clock() - self.session_start_time
        total_alerts = self.alert_stats['total_alerts']
        pages_read = self.reading_stats.get('pages_read', 0)
        reading_speed = pages_read / session_duration * 3600 if session_duration > 0 else 0
        return {
            'session_duration': session_duration,
            'total_blinks': self.eye_tracking_stats.get('total_blinks', 0),
            'total_alerts': total_alerts,
            'pages_read': pages_read,
            'avg_ear': self.eye_tracking_stats.get('avg_ear', 0),
            'attention_score': max(0, 100 - total_alerts * 10),
            'reading_speed': reading_speed,
        }

    def export_to_csv(self, file_path):
        """Exporte les points de données. Lève OSError en cas d'échec d'écriture."""
        fieldnames = ['timestamp', 'ear_avg', 'eye_state', 'current_page', 'alerts_count']
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.data_points)

    def export_to_json(self, file_path):
        """Exporte toute la session. Lève OSError en cas d'échec d'écriture."""
        export_data = {
            'session_info': {
                'start_time': datetime.fromtimestamp(self.session_start_time).isoformat(),
                'duration': self._clock() - self.session_start_time,
            },
            'summary': self.get_summary(),
            'data_points': self.data_points,
            'eye_tracking': self.eye_tracking_stats,
            'reading': self.reading_stats,
            'alerts': self.alert_stats,
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
