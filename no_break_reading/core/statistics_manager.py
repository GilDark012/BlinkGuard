"""
Module de gestion des statistiques
"""

import time
import json
import csv
from datetime import datetime

class StatisticsManager:
    """Gère les statistiques de session"""

    def __init__(self):
        self.session_start_time = time.time()
        self.eye_tracking_stats = {}
        self.reading_stats = {}
        self.alert_stats = {
            'total_alerts': 0,
            'alert_times': []
        }
        self.data_points = []

    def update_eye_tracking(self, eye_data):
        """Met à jour les stats d'eye tracking"""
        self.eye_tracking_stats = eye_data.copy()

    def update_reading(self, pdf_data):
        """Met à jour les stats de lecture"""
        self.reading_stats = pdf_data.copy()

    def update_alert(self, alert_triggered):
        """Enregistre un déclenchement d'alerte"""
        if alert_triggered:
            self.alert_stats['total_alerts'] += 1
            self.alert_stats['alert_times'].append(time.time())

    def add_data_point(self):
        """Ajoute un point de données horodaté"""
        data_point = {
            'timestamp': time.time(),
            'ear_avg': self.eye_tracking_stats.get('avg_ear', 0),
            'eye_state': 'OUVERT',  # À compléter
            'current_page': self.reading_stats.get('current_page', 0),
            'alerts_count': self.alert_stats['total_alerts']
        }
        self.data_points.append(data_point)

    def get_summary(self):
        """Retourne un résumé complet de la session"""
        session_duration = time.time() - self.session_start_time

        total_blinks = self.eye_tracking_stats.get('total_blinks', 0)
        total_alerts = self.alert_stats['total_alerts']
        pages_read = self.reading_stats.get('pages_read', 0)
        avg_ear = self.eye_tracking_stats.get('avg_ear', 0)

        # Score d'attention (0-100, moins d'alertes = meilleur score)
        attention_score = max(0, 100 - (total_alerts * 10))

        # Vitesse de lecture (pages/heure)
        reading_speed = 0
        if session_duration > 0:
            reading_speed = (pages_read / session_duration) * 3600

        return {
            'session_duration': session_duration,
            'total_blinks': total_blinks,
            'total_alerts': total_alerts,
            'pages_read': pages_read,
            'avg_ear': avg_ear,
            'attention_score': attention_score,
            'reading_speed': reading_speed
        }

    def export_to_csv(self, file_path):
        """Exporte les statistiques en CSV"""
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                if not self.data_points:
                    return

                fieldnames = self.data_points[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)

                writer.writeheader()
                writer.writerows(self.data_points)

            return True
        except Exception as e:
            print(f"Erreur export CSV: {e}")
            return False

    def export_to_json(self, file_path):
        """Exporte les statistiques en JSON"""
        try:
            export_data = {
                'session_info': {
                    'start_time': datetime.fromtimestamp(self.session_start_time).isoformat(),
                    'duration': time.time() - self.session_start_time
                },
                'summary': self.get_summary(),
                'data_points': self.data_points,
                'eye_tracking': self.eye_tracking_stats,
                'reading': self.reading_stats,
                'alerts': self.alert_stats
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)

            return True
        except Exception as e:
            print(f"Erreur export JSON: {e}")
            return False

    def generate_report(self):
        """Génère un rapport texte formaté"""
        summary = self.get_summary()

        report = f"""
# Rapport de Session No Break Reading

**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Résumé
- Durée de session: {summary['session_duration']:.0f} secondes
- Clignements totaux: {summary['total_blinks']}
- Alertes déclenchées: {summary['total_alerts']}
- Pages lues: {summary['pages_read']}
- EAR moyen: {summary['avg_ear']:.3f}
- Score d'attention: {summary['attention_score']:.0f}/100
- Vitesse de lecture: {summary['reading_speed']:.1f} pages/heure

## Détails
- Total de points de données: {len(self.data_points)}
        """

        return report

    def reset(self):
        """Réinitialise toutes les statistiques"""
        self.session_start_time = time.time()
        self.eye_tracking_stats = {}
        self.reading_stats = {}
        self.alert_stats = {
            'total_alerts': 0,
            'alert_times': []
        }
        self.data_points = []
