import type { AlertReason } from './alertSystem';
import type { EyeState } from './eyeState';

export interface DataPoint {
  timestamp: string;
  ear: number;
  eyeState: EyeState;
  page: number;
  alerts: number;
}

export interface SessionSummary {
  durationSeconds: number;
  blinks: number;
  alerts: number;
  alertsEyesClosed: number;
  alertsFaceLost: number;
  pagesVisited: number;
  /** Pages visited per hour. */
  readingSpeed: number;
}

/** Session statistics. Kept in memory only, never sent anywhere. */
export class SessionStats {
  readonly dataPoints: DataPoint[] = [];
  readonly alertLog: { timestamp: string; reason: AlertReason }[] = [];
  blinks = 0;
  private readonly visitedPages = new Set<number>();
  private startMs: number;

  constructor(private readonly clock: () => number = Date.now) {
    this.startMs = clock();
  }

  reset(): void {
    this.dataPoints.length = 0;
    this.alertLog.length = 0;
    this.visitedPages.clear();
    this.blinks = 0;
    this.startMs = this.clock();
  }

  visitPage(page: number): void {
    this.visitedPages.add(page);
  }

  recordAlert(reason: AlertReason): void {
    this.alertLog.push({ timestamp: this.isoNow(), reason });
  }

  addDataPoint(point: Omit<DataPoint, 'timestamp' | 'alerts'>): void {
    this.dataPoints.push({
      timestamp: this.isoNow(),
      ear: Math.round(point.ear * 10_000) / 10_000,
      eyeState: point.eyeState,
      page: point.page,
      alerts: this.alertLog.length,
    });
  }

  summary(): SessionSummary {
    const durationSeconds = Math.max(0, (this.clock() - this.startMs) / 1000);
    const pagesVisited = this.visitedPages.size;
    const count = (reason: AlertReason) => this.alertLog.filter((a) => a.reason === reason).length;
    return {
      durationSeconds,
      blinks: this.blinks,
      alerts: this.alertLog.length,
      alertsEyesClosed: count('eyesClosed'),
      alertsFaceLost: count('faceLost'),
      pagesVisited,
      readingSpeed: durationSeconds > 0 ? (pagesVisited / durationSeconds) * 3600 : 0,
    };
  }

  toCsv(): string {
    const header = 'timestamp,ear,eye_state,page,alerts';
    const rows = this.dataPoints.map((p) =>
      [p.timestamp, p.ear, p.eyeState, p.page, p.alerts].map(csvCell).join(','),
    );
    return [header, ...rows].join('\n') + '\n';
  }

  toJson(): string {
    return JSON.stringify(
      {
        session: { start: new Date(this.startMs).toISOString(), summary: this.summary() },
        alerts: this.alertLog,
        dataPoints: this.dataPoints,
      },
      null,
      2,
    );
  }

  private isoNow(): string {
    return new Date(this.clock()).toISOString();
  }
}

function csvCell(value: string | number): string {
  const text = String(value);
  return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}
