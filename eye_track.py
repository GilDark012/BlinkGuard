# Installation requise : pip install opencv-python mediapipe numpy

import cv2
import mediapipe as mp
import numpy as np

# Initialisation de MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils

# Indices des landmarks pour calculer l'EAR (Eye Aspect Ratio)
# Format: [coin externe, haut1, haut2, coin interne, bas1, bas2]
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

# Indices plus précis pour l'EAR
LEFT_EYE_VERTICAL_1 = [159, 145]  # Points verticaux supérieur/inférieur
LEFT_EYE_VERTICAL_2 = [158, 153]
LEFT_EYE_HORIZONTAL = [33, 133]   # Points horizontaux externe/interne

RIGHT_EYE_VERTICAL_1 = [386, 374]
RIGHT_EYE_VERTICAL_2 = [385, 380]
RIGHT_EYE_HORIZONTAL = [362, 263]

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

def get_eye_state(ear, threshold=0.21):
    """Détermine si l'œil est ouvert ou fermé"""
    if ear < threshold:
        return "FERME", (0, 0, 255)  # Rouge
    else:
        return "OUVERT", (0, 255, 0)  # Vert

def main():
    # Paramètres
    EAR_THRESHOLD = 0.21  # Seuil de détection (ajustable)
    
    # Compteurs
    frame_counter = 0
    blink_counter = 0
    eye_closed_frames = 0
    
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
                    
                    previous_state = eye_state
                    
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
                    
                    # Alerte si les yeux sont fermés trop longtemps
                    if eye_closed_frames > 20:  # Environ 0.7 secondes à 30 fps
                        cv2.putText(frame, "ALERTE: YEUX FERMES!", (w//2 - 200, h//2),
                                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 4)
                    
                    # Afficher le seuil
                    cv2.putText(frame, f"Seuil: {EAR_THRESHOLD}", (20, h - 20),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
            
            else:
                cv2.putText(frame, "Aucun visage detecte", (20, 50),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            # Afficher l'image
            cv2.imshow('Detection Yeux Ouverts/Fermes - Q pour quitter', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"\n=== Statistiques ===")
    print(f"Nombre total de clignements: {blink_counter}")
    print(f"Nombre total de frames: {frame_counter}")

if __name__ == "__main__":
    main()
