"""
Module de détection et suivi oculaire
"""

import cv2
import mediapipe as mp
import numpy as np
from config import LEFT_EYE_LANDMARKS, RIGHT_EYE_LANDMARKS, COLOR_OPEN, COLOR_CLOSED

class EyeTracker:
    """Gère la détection des yeux et le calcul de l'EAR"""

    def __init__(self, ear_threshold=0.21, min_detection_confidence=0.5):
        self.ear_threshold = ear_threshold
        self.min_detection_confidence = min_detection_confidence

        # MediaPipe
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = None

        # Statistiques
        self.closed_frames_counter = 0
        self.blink_counter = 0
        self.total_frames = 0
        self.current_ear_left = 0.0
        self.current_ear_right = 0.0
        self.current_ear_avg = 0.0
        self.eye_state = "INACTIF"
        self.previous_state = "OUVERT"

        self.is_active = False

    def start(self):
        """Démarre le tracker"""
        try:
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=self.min_detection_confidence,
                min_tracking_confidence=0.5
            )
            self.is_active = True
            return True
        except Exception as e:
            print(f"Erreur démarrage eye tracker: {e}")
            return False

    def stop(self):
        """Arrête le tracker"""
        if self.face_mesh:
            self.face_mesh.close()
        self.is_active = False

    def process_frame(self, frame):
        """
        Traite une frame et retourne les résultats

        Returns:
            dict avec frame annotée et données eye tracking
        """
        if not self.is_active or self.face_mesh is None:
            return {
                'frame': frame,
                'eye_state': 'INACTIF',
                'ear_left': 0.0,
                'ear_right': 0.0,
                'ear_avg': 0.0,
                'blink_detected': False,
                'closed_duration': 0,
                'face_detected': False
            }

        self.total_frames += 1
        h, w, _ = frame.shape

        # Convertir en RGB pour MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)

        blink_detected = False
        face_detected = False

        if results.multi_face_landmarks:
            face_detected = True

            for face_landmarks in results.multi_face_landmarks:
                # Extraire landmarks des yeux
                left_eye_coords = self._extract_eye_landmarks(
                    face_landmarks, LEFT_EYE_LANDMARKS, w, h
                )
                right_eye_coords = self._extract_eye_landmarks(
                    face_landmarks, RIGHT_EYE_LANDMARKS, w, h
                )

                # Calculer EAR
                self.current_ear_left = self._calculate_ear(left_eye_coords)
                self.current_ear_right = self._calculate_ear(right_eye_coords)
                self.current_ear_avg = (self.current_ear_left + self.current_ear_right) / 2.0

                # Déterminer état
                if self.current_ear_avg < self.ear_threshold:
                    self.eye_state = "FERME"
                    self.closed_frames_counter += 1
                    color = COLOR_CLOSED
                else:
                    self.eye_state = "OUVERT"
                    self.closed_frames_counter = 0
                    color = COLOR_OPEN

                # Détecter clignement
                if self.eye_state == "FERME" and self.previous_state == "OUVERT":
                    self.blink_counter += 1
                    blink_detected = True

                self.previous_state = self.eye_state

                # Annoter la frame
                self._draw_eye_annotations(frame, left_eye_coords, right_eye_coords, color)

                # Afficher infos sur la frame
                cv2.putText(frame, f"Etat: {self.eye_state}", (20, 40),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)
                cv2.putText(frame, f"EAR: {self.current_ear_avg:.3f}", (20, 80),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        return {
            'frame': frame,
            'eye_state': self.eye_state,
            'ear_left': self.current_ear_left,
            'ear_right': self.current_ear_right,
            'ear_avg': self.current_ear_avg,
            'blink_detected': blink_detected,
            'closed_duration': self.closed_frames_counter,
            'face_detected': face_detected,
            'total_blinks': self.blink_counter
        }

    def _extract_eye_landmarks(self, face_landmarks, eye_indices, frame_width, frame_height):
        """Extrait les coordonnées des landmarks d'un œil"""
        coords = []
        for idx in eye_indices:
            landmark = face_landmarks.landmark[idx]
            x = int(landmark.x * frame_width)
            y = int(landmark.y * frame_height)
            coords.append((x, y))
        return coords

    def _calculate_ear(self, eye_coords):
        """
        Calcule l'Eye Aspect Ratio
        EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
        """
        if len(eye_coords) < 6:
            return 0.0

        # Distances verticales
        vertical_1 = np.linalg.norm(np.array(eye_coords[1]) - np.array(eye_coords[5]))
        vertical_2 = np.linalg.norm(np.array(eye_coords[2]) - np.array(eye_coords[4]))

        # Distance horizontale
        horizontal = np.linalg.norm(np.array(eye_coords[0]) - np.array(eye_coords[3]))

        if horizontal == 0:
            return 0.0

        ear = (vertical_1 + vertical_2) / (2.0 * horizontal)
        return ear

    def _draw_eye_annotations(self, frame, left_eye, right_eye, color):
        """Dessine les annotations sur la frame"""
        # Dessiner points des yeux
        for point in left_eye:
            cv2.circle(frame, point, 2, (255, 255, 0), -1)
        for point in right_eye:
            cv2.circle(frame, point, 2, (255, 255, 0), -1)

        # Rectangles autour des yeux
        if left_eye:
            left_x_min = min([pt[0] for pt in left_eye]) - 10
            left_y_min = min([pt[1] for pt in left_eye]) - 10
            left_x_max = max([pt[0] for pt in left_eye]) + 10
            left_y_max = max([pt[1] for pt in left_eye]) + 10
            cv2.rectangle(frame, (left_x_min, left_y_min), 
                         (left_x_max, left_y_max), color, 2)

        if right_eye:
            right_x_min = min([pt[0] for pt in right_eye]) - 10
            right_y_min = min([pt[1] for pt in right_eye]) - 10
            right_x_max = max([pt[0] for pt in right_eye]) + 10
            right_y_max = max([pt[1] for pt in right_eye]) + 10
            cv2.rectangle(frame, (right_x_min, right_y_min), 
                         (right_x_max, right_y_max), color, 2)

    def update_threshold(self, new_threshold):
        """Met à jour le seuil EAR"""
        self.ear_threshold = new_threshold

    def get_statistics(self):
        """Retourne les statistiques courantes"""
        blink_rate = 0
        if self.total_frames > 0:
            # Estimation blinks/minute (en assumant 30 fps)
            seconds = self.total_frames / 30.0
            if seconds > 0:
                blink_rate = (self.blink_counter / seconds) * 60

        return {
            'total_blinks': self.blink_counter,
            'total_frames': self.total_frames,
            'avg_ear': self.current_ear_avg,
            'blink_rate': blink_rate
        }

    def reset_statistics(self):
        """Réinitialise les compteurs"""
        self.closed_frames_counter = 0
        self.blink_counter = 0
        self.total_frames = 0
        self.previous_state = "OUVERT"
