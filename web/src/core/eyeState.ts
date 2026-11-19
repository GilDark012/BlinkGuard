/**
 * Turns a stream of EAR values into an eye state, measured in seconds
 * (not frames), so thresholds stay the same at 10 or 60 FPS.
 */

export type EyeState = 'inactive' | 'open' | 'closed' | 'noFace';

export class EyeStateTracker {
  state: EyeState = 'inactive';
  blinks = 0;
  ear = 0;

  private closedSince: number | null = null;
  private faceMissingSince: number | null = null;
  private sessionStart: number | null = null;

  constructor(public threshold: number) {}

  start(now: number): void {
    this.state = 'open';
    this.blinks = 0;
    this.ear = 0;
    this.sessionStart = now;
    this.clearTimers();
  }

  stop(): void {
    this.state = 'inactive';
    this.clearTimers();
  }

  /** Forget running timers, e.g. when the tab was hidden and no frames were seen. */
  clearTimers(): void {
    this.closedSince = null;
    this.faceMissingSince = null;
  }

  /**
   * @param ear average EAR of both eyes, or null when no face is detected
   * @returns true when a blink (open -> closed) was just detected
   */
  update(ear: number | null, now: number): boolean {
    if (this.state === 'inactive') return false;

    if (ear === null) {
      // Face lost: we can no longer tell whether the eyes are closed.
      this.faceMissingSince ??= now;
      this.closedSince = null;
      this.state = 'noFace';
      return false;
    }

    this.faceMissingSince = null;
    this.ear = ear;

    if (ear < this.threshold) {
      let blink = false;
      if (this.state !== 'closed') {
        this.closedSince = now;
        if (this.state === 'open') {
          this.blinks += 1;
          blink = true;
        }
      }
      this.state = 'closed';
      return blink;
    }

    this.closedSince = null;
    this.state = 'open';
    return false;
  }

  closedSeconds(now: number): number {
    return this.closedSince === null ? 0 : Math.max(0, now - this.closedSince);
  }

  faceMissingSeconds(now: number): number {
    return this.faceMissingSince === null ? 0 : Math.max(0, now - this.faceMissingSince);
  }

  /** Blinks per minute since start. */
  blinkRate(now: number): number {
    if (this.sessionStart === null) return 0;
    const elapsed = now - this.sessionStart;
    return elapsed > 0 ? (this.blinks / elapsed) * 60 : 0;
  }
}
