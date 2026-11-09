"""
Module de détection et suivi oculaire.

Toutes les durées sont mesurées en secondes (horloge monotone) et non en
nombre d'images : le seuil d'alerte reste le même que la webcam tourne à
10 ou à 30 FPS.
"""

import time

import cv2
import numpy as np

from config import LEFT_EYE_LANDMARKS, RIGHT_EYE_LANDMARKS, COLOR_OPEN, COLOR_CLOSED, COLOR_WARNING

STATE_INACTIVE = "INACTIF"
STATE_OPEN = "OUVERT"
STATE_CLOSED = "FERME"
STATE_NO_FACE = "VISAGE ABSENT"


def calculate_ear(eye_coords):
    """
    Eye Aspect Ratio : EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)

    eye_coords: 6 points (x, y) dans l'ordre [coin ext, haut1, haut2, coin int, bas1, bas2]
    """
    if len(eye_coords) < 6:
        return 0.0
    p = np.asarray(eye_coords[:6], dtype=float)
    horizontal = np.linalg.norm(p[0] - p[3])
    if horizontal == 0:
        return 0.0
    vertical_1 = np.linalg.norm(p[1] - p[5])
    vertical_2 = np.linalg.norm(p[2] - p[4])
    return float((vertical_1 + vertical_2) / (2.0 * horizontal))


class EyeTrackerError(RuntimeError):
    """Le moteur de détection (MediaPipe) n'a pas pu démarrer."""


class EyeTracker:
    """Gère la détection des yeux et le calcul de l'EAR"""

    def __init__(self, ear_threshold=0.21, min_detection_confidence=0.5,
                 min_tracking_confidence=0.5, clock=time.monotonic):
        self.ear_threshold = ear_threshold
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self._clock = clock

        self.face_mesh = None
        self.is_active = False
        self.reset_statistics()

    # ------------------------------------------------------------------ cycle de vie

    def start(self):
        """
        Démarre le tracker.

        Raises:
            EyeTrackerError: si MediaPipe est absent ou incompatible.
        """
        try:
            import mediapipe as mp
            face_mesh_module = mp.solutions.face_mesh
        except (ImportError, AttributeError) as e:
            raise EyeTrackerError(
                "MediaPipe est absent ou trop récent (l'API 'solutions' a été retirée).\n"
                "Installez la version prévue : pip install -r requirements.txt\n"
                f"Détail : {e}"
            ) from e
        try:
            self.face_mesh = face_mesh_module.FaceMesh(
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=self.min_detection_confidence,
                min_tracking_confidence=self.min_tracking_confidence,
            )
        except Exception as e:
            raise EyeTrackerError(f"Impossible d'initialiser MediaPipe FaceMesh : {e}") from e

        self.is_active = True
        self.session_start = self._clock()
        self._closed_since = None
        self._face_missing_since = None

    def stop(self):
        if self.face_mesh:
            self.face_mesh.close()
            self.face_mesh = None
        self.is_active = False
        self.eye_state = STATE_INACTIVE
        self._closed_since = None
        self._face_missing_since = None

    # ------------------------------------------------------------------ traitement

    def process_frame(self, frame, now=None):
        """Traite une frame BGR et retourne les résultats (frame annotée incluse)."""
        if not self.is_active or self.face_mesh is None:
            return self._result(frame, blink_detected=False, face_detected=False, now=now)

        h, w = frame.shape[:2]
        results = self.face_mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        ear = None
        left_eye = right_eye = None
        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0]
            left_eye = self._extract_eye_landmarks(face_landmarks, LEFT_EYE_LANDMARKS, w, h)
            right_eye = self._extract_eye_landmarks(face_landmarks, RIGHT_EYE_LANDMARKS, w, h)
            self.current_ear_left = calculate_ear(left_eye)
            self.current_ear_right = calculate_ear(right_eye)
            ear = (self.current_ear_left + self.current_ear_right) / 2.0

        blink = self.update_state(ear, now)

        if ear is not None:
            color = COLOR_CLOSED if self.eye_state == STATE_CLOSED else COLOR_OPEN
            self._draw_eye_annotations(frame, left_eye, right_eye, color)
            cv2.putText(frame, f"Etat: {self.eye_state}", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)
            cv2.putText(frame, f"EAR: {self.current_ear_avg:.3f}", (20, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        else:
            cv2.putText(frame, "Visage non detecte", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, COLOR_WARNING, 2)

        return self._result(frame, blink_detected=blink, face_detected=ear is not None, now=now)

    def update_state(self, ear, now=None):
        """
        Met à jour l'état à partir de l'EAR moyen (None = aucun visage détecté).

        Returns:
            bool: True si un clignement (passage ouvert -> fermé) vient d'être détecté
        """
        now = self._clock() if now is None else now
        self.total_frames += 1

        if ear is None:
            # Visage perdu : on ne sait plus si les yeux sont fermés.
            if self._face_missing_since is None:
                self._face_missing_since = now
            self._closed_since = None
            self.eye_state = STATE_NO_FACE
            return False

        self._face_missing_since = None
        self.current_ear_avg = ear

        blink = False
        if ear < self.ear_threshold:
            if self.eye_state != STATE_CLOSED:
                self._closed_since = now
                if self.eye_state == STATE_OPEN:
                    self.blink_counter += 1
                    blink = True
            self.eye_state = STATE_CLOSED
        else:
            self._closed_since = None
            self.eye_state = STATE_OPEN
        return blink

    def closed_seconds(self, now=None):
        if self._closed_since is None:
            return 0.0
        now = self._clock() if now is None else now
        return max(0.0, now - self._closed_since)

    def face_missing_seconds(self, now=None):
        if self._face_missing_since is None:
            return 0.0
        now = self._clock() if now is None else now
        return max(0.0, now - self._face_missing_since)

    def _result(self, frame, blink_detected, face_detected, now=None):
        now = self._clock() if now is None else now
        return {
            'frame': frame,
            'eye_state': self.eye_state,
            'ear_left': self.current_ear_left,
            'ear_right': self.current_ear_right,
            'ear_avg': self.current_ear_avg,
            'blink_detected': blink_detected,
            'closed_seconds': self.closed_seconds(now),
            'face_missing_seconds': self.face_missing_seconds(now),
            'face_detected': face_detected,
            'total_blinks': self.blink_counter,
        }

    @staticmethod
    def _extract_eye_landmarks(face_landmarks, eye_indices, frame_width, frame_height):
        return [
            (int(face_landmarks.landmark[idx].x * frame_width),
             int(face_landmarks.landmark[idx].y * frame_height))
            for idx in eye_indices
        ]

    @staticmethod
    def _draw_eye_annotations(frame, left_eye, right_eye, color):
        for eye in (left_eye, right_eye):
            if not eye:
                continue
            for point in eye:
                cv2.circle(frame, point, 2, (255, 255, 0), -1)
            xs = [pt[0] for pt in eye]
            ys = [pt[1] for pt in eye]
            cv2.rectangle(frame, (min(xs) - 10, min(ys) - 10),
                          (max(xs) + 10, max(ys) + 10), color, 2)

    # ------------------------------------------------------------------ réglages / stats

    def update_threshold(self, new_threshold):
        self.ear_threshold = new_threshold

    def get_statistics(self, now=None):
        blink_rate = 0.0
        if self.session_start is not None:
            now = self._clock() if now is None else now
            elapsed = now - self.session_start
            if elapsed > 0:
                blink_rate = self.blink_counter / elapsed * 60
        return {
            'total_blinks': self.blink_counter,
            'total_frames': self.total_frames,
            'avg_ear': self.current_ear_avg,
            'blink_rate': blink_rate,
        }

    def reset_statistics(self):
        self.blink_counter = 0
        self.total_frames = 0
        self.current_ear_left = 0.0
        self.current_ear_right = 0.0
        self.current_ear_avg = 0.0
        self.eye_state = STATE_OPEN if self.is_active else STATE_INACTIVE
        self.session_start = self._clock() if self.is_active else None
        self._closed_since = None
        self._face_missing_since = None
