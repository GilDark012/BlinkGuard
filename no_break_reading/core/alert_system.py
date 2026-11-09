"""
Module de gestion des alertes sonores
"""

import pygame
import numpy as np
import time
import threading

class AlertSystem:
    """Gère les alertes sonores quand les yeux sont fermés"""

    def __init__(self, trigger_frames=20, duration=3.0, cooldown=10.0):
        self.alert_trigger_frames = trigger_frames
        self.alert_duration = duration
        self.alert_cooldown = cooldown
        self.alert_frequency = 800

        self.last_alert_time = 0
        self.alert_active = False
        self.sound_enabled = True

        # Initialiser pygame mixer
        try:
            pygame.mixer.init()
        except Exception as e:
            print(f"Avertissement: Pygame mixer non disponible: {e}")
            self.sound_enabled = False

    def check_and_trigger(self, closed_frames):
        """
        Vérifie si une alerte doit être déclenchée

        Args:
            closed_frames: Nombre de frames consécutives avec yeux fermés

        Returns:
            bool: True si alerte déclenchée
        """
        if not self.sound_enabled:
            return False

        current_time = time.time()
        time_since_last_alert = current_time - self.last_alert_time

        # Vérifier si on doit déclencher
        if closed_frames >= self.alert_trigger_frames and not self.alert_active:
            # Vérifier le cooldown
            if time_since_last_alert >= self.alert_cooldown:
                self.play_alert_async()
                self.last_alert_time = current_time
                self.alert_active = True
                return True

        # Réinitialiser alert_active si les yeux sont ouverts
        if closed_frames == 0:
            self.alert_active = False

        return False

    def _generate_beep_sound(self, duration, frequency):
        """Génère un son de bip avec modulation"""
        try:
            sample_rate = 22050

            # Générer signal avec modulation
            t = np.linspace(0, duration, int(sample_rate * duration))
            wave = np.sin(2 * np.pi * frequency * t) * np.sin(2 * np.pi * 3 * t)

            # Envelope pour éviter les clics
            envelope = np.ones_like(t)
            fade_samples = int(0.1 * sample_rate)
            envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
            envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)

            wave = wave * envelope

            # Normaliser et convertir
            wave = (wave * 0.3 * 32767).astype(np.int16)
            stereo_wave = np.column_stack((wave, wave))

            # Jouer
            sound = pygame.sndarray.make_sound(stereo_wave)
            sound.play()
            time.sleep(duration)
        except Exception as e:
            print(f"Erreur génération son: {e}")

    def play_alert_async(self):
        """Lance l'alerte dans un thread séparé"""
        thread = threading.Thread(
            target=self._generate_beep_sound,
            args=(self.alert_duration, self.alert_frequency)
        )
        thread.daemon = True
        thread.start()

    def get_cooldown_remaining(self):
        """Retourne le temps restant avant prochaine alerte"""
        if self.last_alert_time == 0:
            return 0.0

        current_time = time.time()
        time_since_last = current_time - self.last_alert_time
        remaining = max(0, self.alert_cooldown - time_since_last)
        return remaining

    def enable_sound(self):
        """Active les alertes sonores"""
        self.sound_enabled = True

    def disable_sound(self):
        """Désactive les alertes sonores"""
        self.sound_enabled = False

    def update_settings(self, trigger_frames=None, duration=None, cooldown=None, frequency=None):
        """Met à jour les paramètres"""
        if trigger_frames is not None:
            self.alert_trigger_frames = trigger_frames
        if duration is not None:
            self.alert_duration = duration
        if cooldown is not None:
            self.alert_cooldown = cooldown
        if frequency is not None:
            self.alert_frequency = frequency

    def shutdown(self):
        """Libère les ressources"""
        try:
            pygame.mixer.quit()
        except:
            pass
