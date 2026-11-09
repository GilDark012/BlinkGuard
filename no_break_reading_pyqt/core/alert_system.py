"""
Module de gestion des alertes sonores - Version améliorée
Alerte progressive avec volume croissant
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

        # Nouveau: Système d'intensification progressive
        self.alert_count = 0  # Compteur d'alertes consécutives
        self.volume_multiplier = 1.0  # Multiplicateur de volume
        self.max_volume_multiplier = 3.0  # Maximum 300% du volume initial
        self.volume_increase = 0.2  # Augmentation de 20% à chaque alerte

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
        if closed_frames >= self.alert_trigger_frames:
            # Cooldown respecté OU yeux toujours fermés après cooldown
            if time_since_last_alert >= self.alert_cooldown or not self.alert_active:
                if time_since_last_alert >= self.alert_cooldown:
                    # Nouvelle série d'alertes - augmenter l'intensité
                    self.alert_count += 1
                    self.volume_multiplier = min(
                        1.0 + (self.alert_count * self.volume_increase),
                        self.max_volume_multiplier
                    )

                self.play_alert_async()
                self.last_alert_time = current_time
                self.alert_active = True
                return True

        # Réinitialiser le compteur si les yeux sont ouverts assez longtemps
        if closed_frames == 0:
            self.alert_active = False
            # Réinitialiser après 5 secondes sans alerte
            if time_since_last_alert > 5.0:
                self.alert_count = 0
                self.volume_multiplier = 1.0

        return False

    def _generate_beep_sound(self, duration, frequency):
        """Génère un son de bip avec modulation et volume progressif"""
        try:
            sample_rate = 22050

            # Générer signal avec modulation plus agressive si volume augmenté
            t = np.linspace(0, duration, int(sample_rate * duration))

            # Variation de fréquence pour rendre plus urgent
            freq_variation = 1.0 + (self.volume_multiplier - 1.0) * 0.5
            base_wave = np.sin(2 * np.pi * frequency * freq_variation * t)
            modulation = np.sin(2 * np.pi * 3 * t)

            # Si volume augmenté, ajouter harmoniques pour son plus strident
            if self.volume_multiplier > 1.5:
                harmonic = np.sin(2 * np.pi * frequency * 2 * t) * 0.3
                wave = base_wave * modulation + harmonic
            else:
                wave = base_wave * modulation

            # Envelope pour éviter les clics
            envelope = np.ones_like(t)
            fade_samples = int(0.1 * sample_rate)
            envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
            envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)

            wave = wave * envelope

            # Appliquer le volume progressif (limité pour ne pas saturer)
            volume = min(0.3 * self.volume_multiplier, 0.9)
            wave = (wave * volume * 32767).astype(np.int16)
            stereo_wave = np.column_stack((wave, wave))

            # Jouer
            sound = pygame.sndarray.make_sound(stereo_wave)
            sound.play()

            # Afficher le niveau d'alerte
            intensity_pct = int(self.volume_multiplier * 100)
            print(f"🔔 ALERTE #{self.alert_count} - Intensité: {intensity_pct}%")

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

    def get_alert_intensity(self):
        """Retourne l'intensité actuelle de l'alerte (1.0 à 3.0)"""
        return self.volume_multiplier

    def get_alert_count(self):
        """Retourne le nombre d'alertes consécutives"""
        return self.alert_count

    def reset_intensity(self):
        """Réinitialise manuellement l'intensité"""
        self.alert_count = 0
        self.volume_multiplier = 1.0

    def enable_sound(self):
        """Active les alertes sonores"""
        self.sound_enabled = True

    def disable_sound(self):
        """Désactive les alertes sonores"""
        self.sound_enabled = False

    def update_settings(self, trigger_frames=None, duration=None, cooldown=None, 
                       frequency=None, volume_increase=None, max_volume=None):
        """Met à jour les paramètres"""
        if trigger_frames is not None:
            self.alert_trigger_frames = trigger_frames
        if duration is not None:
            self.alert_duration = duration
        if cooldown is not None:
            self.alert_cooldown = cooldown
        if frequency is not None:
            self.alert_frequency = frequency
        if volume_increase is not None:
            self.volume_increase = volume_increase
        if max_volume is not None:
            self.max_volume_multiplier = max_volume

    def shutdown(self):
        """Libère les ressources"""
        try:
            pygame.mixer.quit()
        except:
            pass
