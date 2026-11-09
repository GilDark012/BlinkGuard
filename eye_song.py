# Installation requise : pip install opencv-python mediapipe numpy pygame

import cv2
import mediapipe as mp
import numpy as np
import pygame
import time
import threading

# Initialisation de MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils

# Initialisation de Pygame pour le son
pygame.mixer.init()

# Indices des landmarks pour calculer l'EAR (Eye Aspect Ratio)
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

def calculate_distance(point1, point2):
    """Calcule la distance euclidienne entre deux points"""
    return np.linalg.norm(np.array(point1) - np.array(point2))

def calculate_eye_aspect_ratio(eye_landmarks):
    """
    Calcule l'Eye Aspect Ratio (EAR)
    EAR = (dist_vertical_1 + dist_vertical_2) / (2 * dist_horizontal)
    """
    # Distances verticales
    vertical_1 = calculate_distance(eye_landmarks[1], eye_landmarks[5])
    vertical_2 = calculate_distance(eye_landmarks[2], eye_landmarks[4])
    
    # Distance horizontale
    horizontal = calculate_distance(eye_landmarks[0], eye_landmarks[3])
    
    # Calcul de l'EAR
    if horizontal > 0:
        ear = (vertical_1 + vertical_2) / (2.0 * horizontal)
    else:
        ear = 0
    
    return ear

def generate_beep_sound(duration=3.0, frequency=800):
    """
    Génère et joue un son de bip pendant une durée spécifiée
    """
    sample_rate = 22050
    
    # Générer un son avec variation de fréquence pour le rendre plus audible
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Créer une onde avec modulation pour attirer l'attention
    wave = np.sin(2 * np.pi * frequency * t) * np.sin(2 * np.pi * 3 * t)
    
    # Ajouter une enveloppe pour éviter les clics
    envelope = np.ones_like(t)
    fade_samples = int(0.1 * sample_rate)  # 100ms de fade in/out
    envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
    envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
    
    wave = wave * envelope
    
    # Normaliser et convertir en format audio
    wave = (wave * 0.3 * 32767).astype(np.int16)
    stereo_wave = np.column_stack((wave, wave))
    
    # Créer et jouer le son
    sound = pygame.sndarray.make_sound(stereo_wave)
    sound.play()
    
    # Attendre la fin de la lecture
    time.sleep(duration)

def play_alert_sound_async(duration=3.0):
    """Lance l'alerte sonore dans un thread séparé pour ne pas bloquer la vidéo"""
    thread = threading.Thread(target=generate_beep_sound, args=(duration,))
    thread.daemon = True
    thread.start()

def get_eye_state(ear, threshold=0.21):
    """Détermine si l'œil est ouvert ou fermé"""
    if ear < threshold:
        return "FERME", (0, 0, 255)  # Rouge
    else:
        return "OUVERT", (0, 255, 0)  # Vert

def main():
    # Paramètres
    EAR_THRESHOLD = 0.21  # Seuil de détection (ajustable)
    ALERT_TRIGGER_FRAMES = 20  # Frames avant déclenchement alerte (~0.7s à 30fps)
    ALERT_DURATION = 3.0  # Durée de l'alerte sonore en secondes
    ALERT_COOLDOWN = 5.0  # Temps d'attente avant nouvelle alerte en secondes
    
    # Compteurs et variables de timing
    frame_counter = 0
    blink_counter = 0
    eye_closed_frames = 0
    last_alert_time = 0
    alert_active = False
    
    cap = cv2.VideoCapture(0)
    
    # Variables pour détecter les clignements
    previous_state = "OUVERT"
    
    with mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as face_mesh:
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("Impossible de lire la webcam")
                break
            
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            frame_counter += 1
            current_time = time.time()
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb_frame)
            
            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    # Extraire les coordonnées de l'œil gauche
                    left_eye_coords = []
                    for idx in LEFT_EYE:
                        landmark = face_landmarks.landmark[idx]
                        x = int(landmark.x * w)
                        y = int(landmark.y * h)
                        left_eye_coords.append((x, y))
                    
                    # Extraire les coordonnées de l'œil droit
                    right_eye_coords = []
                    for idx in RIGHT_EYE:
                        landmark = face_landmarks.landmark[idx]
                        x = int(landmark.x * w)
                        y = int(landmark.y * h)
                        right_eye_coords.append((x, y))
                    
                    # Dessiner les contours des yeux
                    for point in left_eye_coords:
                        cv2.circle(frame, point, 2, (255, 255, 0), -1)
                    for point in right_eye_coords:
                        cv2.circle(frame, point, 2, (255, 255, 0), -1)
                    
                    # Calculer l'EAR pour chaque œil
                    left_ear = calculate_eye_aspect_ratio(left_eye_coords)
                    right_ear = calculate_eye_aspect_ratio(right_eye_coords)
                    
                    # Moyenne des deux yeux
                    avg_ear = (left_ear + right_ear) / 2.0
                    
                    # Déterminer l'état des yeux
                    eye_state, color = get_eye_state(avg_ear, EAR_THRESHOLD)
                    
                    # Compter les clignements
                    if eye_state == "FERME" and previous_state == "OUVERT":
                        blink_counter += 1
                    
                    # Compter les frames avec yeux fermés
                    if eye_state == "FERME":
                        eye_closed_frames += 1
                    else:
                        eye_closed_frames = 0
                        alert_active = False
                    
                    previous_state = eye_state
                    
                    # Gestion de l'alerte sonore
                    time_since_last_alert = current_time - last_alert_time
                    
                    if eye_closed_frames >= ALERT_TRIGGER_FRAMES and not alert_active:
                        # Vérifier le cooldown
                        if time_since_last_alert >= ALERT_COOLDOWN:
                            print(f"[ALERTE] Yeux fermés détectés ! Déclenchement de l'alarme...")
                            play_alert_sound_async(ALERT_DURATION)
                            last_alert_time = current_time
                            alert_active = True
                    
                    # Dessiner un rectangle autour de chaque œil avec couleur selon l'état
                    # Œil gauche
                    left_x_min = min([pt[0] for pt in left_eye_coords]) - 10
                    left_y_min = min([pt[1] for pt in left_eye_coords]) - 10
                    left_x_max = max([pt[0] for pt in left_eye_coords]) + 10
                    left_y_max = max([pt[1] for pt in left_eye_coords]) + 10
                    cv2.rectangle(frame, (left_x_min, left_y_min), 
                                (left_x_max, left_y_max), color, 2)
                    
                    # Œil droit
                    right_x_min = min([pt[0] for pt in right_eye_coords]) - 10
                    right_y_min = min([pt[1] for pt in right_eye_coords]) - 10
                    right_x_max = max([pt[0] for pt in right_eye_coords]) + 10
                    right_y_max = max([pt[1] for pt in right_eye_coords]) + 10
                    cv2.rectangle(frame, (right_x_min, right_y_min), 
                                (right_x_max, right_y_max), color, 2)
                    
                    # Afficher les informations
                    cv2.putText(frame, f"Etat: {eye_state}", (20, 50),
                               cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)
                    
                    cv2.putText(frame, f"EAR Gauche: {left_ear:.3f}", (20, 100),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    
                    cv2.putText(frame, f"EAR Droit: {right_ear:.3f}", (20, 130),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    
                    cv2.putText(frame, f"EAR Moyen: {avg_ear:.3f}", (20, 160),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                    
                    cv2.putText(frame, f"Clignements: {blink_counter}", (20, 200),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                    
                    cv2.putText(frame, f"Frames yeux fermes: {eye_closed_frames}", (20, 240),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                    
                    # Afficher le temps depuis la dernière alerte
                    if last_alert_time > 0:
                        remaining_cooldown = max(0, ALERT_COOLDOWN - time_since_last_alert)
                        cv2.putText(frame, f"Cooldown: {remaining_cooldown:.1f}s", (20, 280),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 165, 0), 2)
                    
                    # Alerte visuelle si les yeux sont fermés trop longtemps
                    if eye_closed_frames >= ALERT_TRIGGER_FRAMES:
                        # Animation clignotante
                        if frame_counter % 20 < 10:
                            cv2.putText(frame, "ALERTE: REVEILLEZ-VOUS!", (w//2 - 250, h//2),
                                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 4)
                            # Rectangle rouge clignotant autour de l'écran
                            cv2.rectangle(frame, (5, 5), (w-5, h-5), (0, 0, 255), 10)
                    
                    # Afficher le seuil
                    cv2.putText(frame, f"Seuil EAR: {EAR_THRESHOLD}", (20, h - 60),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
                    cv2.putText(frame, f"Duree alerte: {ALERT_DURATION}s", (20, h - 35),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
                    cv2.putText(frame, f"Cooldown: {ALERT_COOLDOWN}s", (20, h - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
            
            else:
                cv2.putText(frame, "Aucun visage detecte", (20, 50),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            # Afficher l'image
            cv2.imshow('Detection Yeux Ouverts/Fermes avec Alerte Sonore - Q pour quitter', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    cap.release()
    cv2.destroyAllWindows()
    pygame.mixer.quit()
    
    print(f"\n=== Statistiques ===")
    print(f"Nombre total de clignements: {blink_counter}")
    print(f"Nombre total de frames: {frame_counter}")

if __name__ == "__main__":
    main()
