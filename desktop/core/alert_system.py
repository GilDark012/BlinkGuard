"""
Module de gestion des alertes sonores.

La logique (quand sonner, à quelle intensité) est séparée de la lecture du son
pour pouvoir être testée avec une horloge simulée.

Règles :
- Une alerte se déclenche quand les yeux sont fermés depuis `trigger_seconds`
  (ou que le visage a disparu depuis `face_lost_seconds`).
- Le son dure `duration` s, puis on attend `cooldown` s avant de pouvoir
  relancer. Une brève réouverture des yeux ne contourne PAS ce délai.
- Chaque alerte d'un même épisode est `volume_increase` plus forte (plafonnée).
- L'épisode se termine quand les yeux restent ouverts `reset_after` s :
  l'intensité revient alors à 100%.
"""

import time

import numpy as np

REASON_EYES_CLOSED = "eyes_closed"
REASON_FACE_LOST = "face_lost"


class AlertSystem:
    """Décide quand alerter et joue le son correspondant."""

    def __init__(self, trigger_seconds=1.0, duration=3.0, cooldown=10.0,
                 reset_after=5.0, face_lost_alert=True, face_lost_seconds=5.0,
                 frequency=800, volume_increase=0.2, max_volume_multiplier=3.0,
                 sound_enabled=True, clock=time.monotonic, audio=True):
        self.trigger_seconds = trigger_seconds
        self.alert_duration = duration
        self.alert_cooldown = cooldown
        self.reset_after = reset_after
        self.face_lost_alert = face_lost_alert
        self.face_lost_seconds = face_lost_seconds
        self.alert_frequency = frequency
        self.volume_increase = volume_increase
        self.max_volume_multiplier = max_volume_multiplier
        self.sound_enabled = sound_enabled
        self._clock = clock

        self.last_alert_time = None
        self.last_reason = None
        self.alert_count = 0          # alertes de l'épisode en cours
        self.volume_multiplier = 1.0
        self._awake_since = None      # début de la période yeux ouverts

        self._mixer = None
        self._current_sound = None    # garde une référence pendant la lecture
        self.audio_error = None
        if audio:
            self._init_mixer()

    # ------------------------------------------------------------------ logique

    def check_and_trigger(self, closed_seconds, face_missing_seconds=0.0, now=None):
        """
        Met à jour l'état et déclenche une alerte si nécessaire.

        Args:
            closed_seconds: durée (s) depuis laquelle les yeux sont fermés, 0 si ouverts
            face_missing_seconds: durée (s) depuis laquelle aucun visage n'est détecté

        Returns:
            bool: True si une nouvelle alerte vient d'être déclenchée
        """
        now = self._clock() if now is None else now

        reason = None
        if closed_seconds >= self.trigger_seconds:
            reason = REASON_EYES_CLOSED
        elif self.face_lost_alert and face_missing_seconds >= self.face_lost_seconds:
            reason = REASON_FACE_LOST

        if reason is None:
            self._track_awake(closed_seconds, face_missing_seconds, now)
            return False

        self._awake_since = None
        if not self._can_alert(now):
            return False

        self.alert_count += 1
        self.volume_multiplier = min(
            1.0 + (self.alert_count - 1) * self.volume_increase,
            self.max_volume_multiplier,
        )
        self.last_alert_time = now
        self.last_reason = reason
        self._play()
        return True

    def _can_alert(self, now):
        if self.last_alert_time is None:
            return True
        return now - self.last_alert_time >= self.alert_duration + self.alert_cooldown

    def _track_awake(self, closed_seconds, face_missing_seconds, now):
        """Termine l'épisode si les yeux restent ouverts assez longtemps."""
        if closed_seconds > 0 or face_missing_seconds > 0:
            self._awake_since = None
            return
        if self._awake_since is None:
            self._awake_since = now
        if self.alert_count and now - self._awake_since >= self.reset_after:
            self.reset_intensity()

    def get_cooldown_remaining(self, now=None):
        """Temps restant (s) avant qu'une nouvelle alerte soit possible."""
        if self.last_alert_time is None:
            return 0.0
        now = self._clock() if now is None else now
        wait = self.alert_duration + self.alert_cooldown
        return max(0.0, wait - (now - self.last_alert_time))

    def is_ringing(self, now=None):
        if self.last_alert_time is None:
            return False
        now = self._clock() if now is None else now
        return now - self.last_alert_time < self.alert_duration

    def get_alert_intensity(self):
        """Intensité actuelle (1.0 à max_volume_multiplier)."""
        return self.volume_multiplier

    def get_alert_count(self):
        """Nombre d'alertes de l'épisode en cours."""
        return self.alert_count

    def reset_intensity(self):
        self.alert_count = 0
        self.volume_multiplier = 1.0

    def reset(self):
        """Réinitialise tout l'état (par ex. à l'arrêt du tracking)."""
        self.stop_sound()
        self.reset_intensity()
        self.last_alert_time = None
        self.last_reason = None
        self._awake_since = None

    # ------------------------------------------------------------------ son

    def _init_mixer(self):
        try:
            import pygame
            pygame.mixer.init()
            self._mixer = pygame
        except Exception as e:  # pas de carte son, pas de pygame...
            self.audio_error = str(e)
            self._mixer = None

    @property
    def audio_available(self):
        return self._mixer is not None

    def build_wave(self, duration, frequency, sample_rate=22050):
        """Génère le signal stéréo int16 de l'alerte pour l'intensité courante."""
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

        # Plus l'intensité monte, plus le son est aigu et strident
        freq_variation = 1.0 + (self.volume_multiplier - 1.0) * 0.5
        wave = np.sin(2 * np.pi * frequency * freq_variation * t)
        wave *= np.sin(2 * np.pi * 3 * t)  # modulation
        if self.volume_multiplier > 1.5:
            wave += np.sin(2 * np.pi * frequency * 2 * t) * 0.3

        # Fondu d'entrée/sortie pour éviter les clics
        fade = min(int(0.1 * sample_rate), len(t) // 2)
        if fade:
            envelope = np.ones_like(t)
            envelope[:fade] = np.linspace(0, 1, fade)
            envelope[-fade:] = np.linspace(1, 0, fade)
            wave *= envelope

        volume = min(0.3 * self.volume_multiplier, 0.9)
        wave = np.clip(wave * volume, -1.0, 1.0)
        mono = (wave * 32767).astype(np.int16)
        return np.ascontiguousarray(np.column_stack((mono, mono)))

    def _play(self):
        if not (self.sound_enabled and self._mixer):
            return
        try:
            self.stop_sound()
            wave = self.build_wave(self.alert_duration, self.alert_frequency)
            self._current_sound = self._mixer.sndarray.make_sound(wave)
            self._current_sound.play()  # non bloquant
        except Exception as e:
            self.audio_error = str(e)

    def stop_sound(self):
        if self._current_sound is not None:
            try:
                self._current_sound.stop()
            except Exception:
                pass
            self._current_sound = None

    def enable_sound(self):
        self.sound_enabled = True

    def disable_sound(self):
        self.sound_enabled = False
        self.stop_sound()

    def update_settings(self, trigger_seconds=None, duration=None, cooldown=None,
                        frequency=None, volume_increase=None, max_volume=None):
        if trigger_seconds is not None:
            self.trigger_seconds = trigger_seconds
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
        self.stop_sound()
        if self._mixer:
            try:
                self._mixer.mixer.quit()
            except Exception:
                pass
