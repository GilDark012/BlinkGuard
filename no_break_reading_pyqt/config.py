"""
Configuration globale pour Wake Reader
"""

# Configuration Eye Tracking
EYE_TRACKING_CONFIG = {
    'ear_threshold': 0.21,
    'min_detection_confidence': 0.5,
    'min_tracking_confidence': 0.5,
    'webcam_index': 0,
    'frame_width': 640,
    'frame_height': 480,
    'fps_target': 30
}

# Configuration Alertes
ALERT_CONFIG = {
    'trigger_frames': 30,      # ~0.7s à 30fps
    'duration': 5.0,           # secondes
    'cooldown': 10.0,          # secondes
    'frequency': 800,          # Hz
    'enabled': True
}

# Configuration PDF
PDF_CONFIG = {
    'default_zoom': 0.5,
    'min_zoom': 0.2,
    'max_zoom': 1.0,
    'auto_scroll_enabled': False,
    'scroll_speed': 5
}

# Configuration Statistiques
STATS_CONFIG = {
    'data_point_interval': 1.0,  # secondes
    'auto_save': True,
    'save_interval': 60.0,       # secondes
    'export_format': 'csv'       # 'csv' | 'json'
}

# Chemins
PATHS = {
    'exports': './exports/',
    'temp': './temp/',
    'logs': './logs/'
}

# Constantes Eye Tracking
LEFT_EYE_LANDMARKS = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_LANDMARKS = [362, 385, 387, 263, 373, 380]

# Couleurs BGR
COLOR_OPEN = (0, 255, 0)   # Vert
COLOR_CLOSED = (0, 0, 255)  # Rouge
COLOR_WARNING = (0, 165, 255)  # Orange
