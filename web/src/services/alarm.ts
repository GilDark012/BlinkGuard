/**
 * Alarm sound synthesised with the Web Audio API (no audio files).
 * Same recipe as desktop v1: a tone pulsing at 3 Hz that gets louder,
 * higher and harsher with each consecutive alert.
 */
export class Alarm {
  muted = false;
  private ctx: AudioContext | null = null;
  private nodes: AudioScheduledSourceNode[] = [];

  /** Must be called from a user gesture (click), or browsers keep audio blocked. */
  async unlock(): Promise<void> {
    this.ctx ??= new AudioContext();
    if (this.ctx.state === 'suspended') await this.ctx.resume();
  }

  get blocked(): boolean {
    return this.ctx !== null && this.ctx.state !== 'running';
  }

  play(multiplier: number, durationSeconds: number, baseFrequency: number): void {
    this.stop();
    const ctx = this.ctx;
    if (this.muted || !ctx || ctx.state !== 'running') return;

    const start = ctx.currentTime;
    const end = start + durationSeconds;
    const volume = Math.min(0.3 * multiplier, 0.9);
    const fade = Math.min(0.1, durationSeconds / 2);

    // Envelope: fade in and out to avoid clicks.
    const master = ctx.createGain();
    master.gain.setValueAtTime(0, start);
    master.gain.linearRampToValueAtTime(volume, start + fade);
    master.gain.setValueAtTime(volume, end - fade);
    master.gain.linearRampToValueAtTime(0, end);
    master.connect(ctx.destination);

    // 3 Hz pulse: the LFO drives the gain between -1 and 1 (ring modulation).
    const pulse = ctx.createGain();
    pulse.gain.value = 0;
    pulse.connect(master);
    const lfo = ctx.createOscillator();
    lfo.frequency.value = 3;
    lfo.connect(pulse.gain);

    const tone = ctx.createOscillator();
    tone.frequency.value = baseFrequency * (1 + (multiplier - 1) * 0.5);
    tone.connect(pulse);
    this.nodes = [lfo, tone];

    if (multiplier > 1.5) {
      const harmonic = ctx.createOscillator();
      harmonic.frequency.value = baseFrequency * 2;
      const harmonicGain = ctx.createGain();
      harmonicGain.gain.value = 0.3;
      harmonic.connect(harmonicGain).connect(pulse);
      this.nodes.push(harmonic);
    }

    for (const node of this.nodes) {
      node.start(start);
      node.stop(end);
    }
  }

  stop(): void {
    for (const node of this.nodes) {
      try {
        node.stop();
      } catch {
        // Already stopped.
      }
    }
    this.nodes = [];
  }
}
