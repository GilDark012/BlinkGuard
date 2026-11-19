/**
 * Decides when to raise an alert and how strong it is. No sound here:
 * the caller plays the alarm, so the rules can be tested with a fake clock.
 *
 * Rules:
 * - Alert when the eyes have been closed for `triggerSeconds`
 *   (or the face has been missing for `faceLostSeconds`).
 * - The sound lasts `duration`, then we wait `cooldown` before the next alert.
 *   Opening the eyes briefly does NOT skip this wait.
 * - Each alert of the same episode is `volumeIncrease` stronger (capped).
 * - The episode ends once the eyes stay open for `resetAfter`: intensity goes back to 100%.
 */

export type AlertReason = 'eyesClosed' | 'faceLost';

export interface AlertOptions {
  triggerSeconds: number;
  duration: number;
  cooldown: number;
  resetAfter: number;
  faceLostAlert: boolean;
  faceLostSeconds: number;
  volumeIncrease: number;
  maxVolumeMultiplier: number;
}

export class AlertSystem {
  alertCount = 0;
  volumeMultiplier = 1;
  lastReason: AlertReason | null = null;

  private lastAlertTime: number | null = null;
  private awakeSince: number | null = null;

  constructor(public options: AlertOptions) {}

  /** @returns true when a new alert was just raised */
  check(closedSeconds: number, faceMissingSeconds: number, now: number): boolean {
    const o = this.options;
    let reason: AlertReason | null = null;
    if (closedSeconds >= o.triggerSeconds) reason = 'eyesClosed';
    else if (o.faceLostAlert && faceMissingSeconds >= o.faceLostSeconds) reason = 'faceLost';

    if (reason === null) {
      this.trackAwake(closedSeconds, faceMissingSeconds, now);
      return false;
    }

    this.awakeSince = null;
    if (!this.canAlert(now)) return false;

    this.alertCount += 1;
    this.volumeMultiplier = Math.min(1 + (this.alertCount - 1) * o.volumeIncrease, o.maxVolumeMultiplier);
    this.lastAlertTime = now;
    this.lastReason = reason;
    return true;
  }

  cooldownRemaining(now: number): number {
    if (this.lastAlertTime === null) return 0;
    const wait = this.options.duration + this.options.cooldown;
    return Math.max(0, wait - (now - this.lastAlertTime));
  }

  isRinging(now: number): boolean {
    return this.lastAlertTime !== null && now - this.lastAlertTime < this.options.duration;
  }

  resetIntensity(): void {
    this.alertCount = 0;
    this.volumeMultiplier = 1;
  }

  /** Clears everything, e.g. when tracking stops. */
  reset(): void {
    this.resetIntensity();
    this.lastAlertTime = null;
    this.lastReason = null;
    this.awakeSince = null;
  }

  private canAlert(now: number): boolean {
    if (this.lastAlertTime === null) return true;
    return now - this.lastAlertTime >= this.options.duration + this.options.cooldown;
  }

  /** Ends the episode once the eyes have stayed open long enough. */
  private trackAwake(closedSeconds: number, faceMissingSeconds: number, now: number): void {
    if (closedSeconds > 0 || faceMissingSeconds > 0) {
      this.awakeSince = null;
      return;
    }
    this.awakeSince ??= now;
    if (this.alertCount > 0 && now - this.awakeSince >= this.options.resetAfter) {
      this.resetIntensity();
    }
  }
}
