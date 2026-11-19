/** All tunable settings. Durations are in seconds. */

export const EYE_CONFIG = {
  earThreshold: 0.21,
  minDetectionConfidence: 0.5,
  minTrackingConfidence: 0.5,
} as const;

export const ALERT_CONFIG = {
  /** Eyes closed for this long -> alert. */
  triggerSeconds: 1.0,
  /** Length of the alarm sound. */
  duration: 5.0,
  /** Pause after the sound before the alarm can ring again. */
  cooldown: 10.0,
  /** Eyes open for this long -> intensity back to 100%. */
  resetAfter: 5.0,
  /** Also alert when the face leaves the camera (head dropping). */
  faceLostAlert: true,
  faceLostSeconds: 5.0,
  /** Base tone, in Hz. */
  frequency: 800,
  /** +20% for each consecutive alert, capped. */
  volumeIncrease: 0.2,
  maxVolumeMultiplier: 3.0,
} as const;

export const PDF_CONFIG = {
  defaultZoom: 1.2,
  minZoom: 0.5,
  maxZoom: 3.0,
  zoomStep: 0.1,
} as const;

export const STATS_CONFIG = {
  dataPointIntervalMs: 1000,
} as const;

/** MediaPipe Face Mesh indices: [outer corner, top 1, top 2, inner corner, bottom 1, bottom 2]. */
export const LEFT_EYE_LANDMARKS = [33, 160, 158, 133, 153, 144] as const;
export const RIGHT_EYE_LANDMARKS = [362, 385, 387, 263, 373, 380] as const;
