"""
Configuration globale pour Wake Reader
"""

# Configuration Eye Tracking
EYE_TRACKING_CONFIG = {
    'ear_threshold': 0.21,
    'min_detection_confidence': 0.5,
    'min_tracking_confidence': 0.5,
    'webcam_index': 0,
    'frame_interval_ms': 33,        # ~30 FPS visés
    'max_read_failures': 30,        # lectures webcam ratées avant arrêt
}

# Configuration Alertes (toutes les durées sont en secondes)
ALERT_CONFIG = {
    'trigger_seconds': 1.0,        # yeux fermés depuis X s -> alerte
    'duration': 5.0,               # durée du son
    'cooldown': 10.0,              # attente après la fin du son avant de relancer
    'reset_after': 5.0,            # yeux ouverts X s -> l'intensité revient à 100%
    'face_lost_alert': True,       # alerter si le visage disparaît (tête qui tombe)
    'face_lost_seconds': 5.0,
    'frequency': 800,              # Hz
    'volume_increase': 0.2,        # +20% par alerte consécutive
    'max_volume_multiplier': 3.0,
    'enabled': True,
}

# Configuration PDF
PDF_CONFIG = {
    'default_zoom': 1.2,
    'min_zoom': 0.5,
    'max_zoom': 3.0,
    'zoom_debounce_ms': 150,
}

# Configuration Statistiques
STATS_CONFIG = {
    'data_point_interval': 1.0,  # secondes
}

# Constantes Eye Tracking
LEFT_EYE_LANDMARKS = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_LANDMARKS = [362, 385, 387, 263, 373, 380]

# Couleurs BGR
COLOR_OPEN = (0, 255, 0)   # Vert
COLOR_CLOSED = (0, 0, 255)  # Rouge
COLOR_WARNING = (0, 165, 255)  # Orange
