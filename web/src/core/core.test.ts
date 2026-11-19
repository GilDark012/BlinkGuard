import { beforeEach, describe, expect, it } from 'vitest';
import { ALERT_CONFIG } from '../config';
import { AlertSystem } from './alertSystem';
import { calculateEar, type Point } from './ear';
import { EyeStateTracker } from './eyeState';
import { SessionStats } from './stats';

const pts = (coords: [number, number][]): Point[] => coords.map(([x, y]) => ({ x, y }));
const OPEN_EYE = pts([[0, 0], [3, -2], [7, -2], [10, 0], [7, 2], [3, 2]]); // EAR 0.4
const CLOSED_EYE = pts([[0, 0], [3, -0.5], [7, -0.5], [10, 0], [7, 0.5], [3, 0.5]]); // EAR 0.1

describe('calculateEar', () => {
  it('measures open and closed eyes', () => {
    expect(calculateEar(OPEN_EYE)).toBeCloseTo(0.4);
    expect(calculateEar(CLOSED_EYE)).toBeCloseTo(0.1);
  });

  it.each([[[]], [pts(Array(5).fill([0, 0]))], [pts(Array(6).fill([1, 1]))]])(
    'returns 0 for degenerate input',
    (eye) => expect(calculateEar(eye)).toBe(0),
  );
});

describe('EyeStateTracker', () => {
  let t: EyeStateTracker;
  beforeEach(() => {
    t = new EyeStateTracker(0.21);
    t.start(1000);
  });

  it('is inactive until started', () => {
    expect(new EyeStateTracker(0.21).state).toBe('inactive');
  });

  it('measures closed time in seconds, not frames', () => {
    t.update(0.3, 1000);
    t.update(0.1, 1000);
    expect(t.state).toBe('closed');
    t.update(0.1, 1001.5);
    expect(t.closedSeconds(1001.5)).toBeCloseTo(1.5);
    t.update(0.3, 1002);
    expect(t.state).toBe('open');
    expect(t.closedSeconds(1002)).toBe(0);
  });

  it('counts one blink per closure', () => {
    expect(t.update(0.3, 1000)).toBe(false);
    expect(t.update(0.1, 1000)).toBe(true);
    expect(t.update(0.1, 1000)).toBe(false);
    t.update(0.3, 1000);
    expect(t.update(0.1, 1000)).toBe(true);
    expect(t.blinks).toBe(2);
  });

  it('tracks a lost face and resets the closed timer', () => {
    t.update(0.1, 1000);
    t.update(null, 1000.5);
    expect(t.state).toBe('noFace');
    expect(t.closedSeconds(1000.5)).toBe(0);
    t.update(null, 1003.5);
    expect(t.faceMissingSeconds(1003.5)).toBeCloseTo(3);
    t.update(0.3, 1004);
    expect(t.faceMissingSeconds(1004)).toBe(0);
  });

  it('computes the blink rate from elapsed time', () => {
    t.update(0.3, 1000);
    t.update(0.1, 1000);
    t.update(0.3, 1000);
    expect(t.blinkRate(1030)).toBeCloseTo(2);
  });

  it('ignores frames once stopped', () => {
    t.stop();
    expect(t.update(0.1, 1001)).toBe(false);
    expect(t.state).toBe('inactive');
  });
});

describe('AlertSystem', () => {
  let a: AlertSystem;
  let now: number;
  beforeEach(() => {
    a = new AlertSystem({ ...ALERT_CONFIG, duration: 3, cooldown: 10, resetAfter: 5, faceLostSeconds: 5 });
    now = 1000;
  });

  it('does not alert before the trigger delay', () => {
    expect(a.check(0.9, 0, now)).toBe(false);
    expect(a.alertCount).toBe(0);
  });

  it('starts at 100% intensity', () => {
    expect(a.check(1, 0, now)).toBe(true);
    expect(a.lastReason).toBe('eyesClosed');
    expect(a.volumeMultiplier).toBeCloseTo(1);
  });

  it('waits duration + cooldown before repeating', () => {
    expect(a.check(1, 0, now)).toBe(true);
    now += 12.9;
    expect(a.check(13.9, 0, now)).toBe(false);
    expect(a.cooldownRemaining(now)).toBeCloseTo(0.1);
    now += 0.1;
    expect(a.check(14, 0, now)).toBe(true);
    expect(a.volumeMultiplier).toBeCloseTo(1.2);
  });

  it('does not let a brief eye opening skip the cooldown', () => {
    expect(a.check(1, 0, now)).toBe(true);
    now += 2;
    expect(a.check(0, 0, now)).toBe(false);
    now += 1;
    expect(a.check(1, 0, now)).toBe(false);
    expect(a.alertCount).toBe(1);
  });

  it('escalates intensity up to the cap', () => {
    a.options.maxVolumeMultiplier = 1.5;
    for (const expected of [1, 1.2, 1.4, 1.5, 1.5]) {
      expect(a.check(5, 0, now)).toBe(true);
      expect(a.volumeMultiplier).toBeCloseTo(expected);
      now += 13;
    }
  });

  it('resets intensity once the eyes stay open long enough', () => {
    a.check(1, 0, now);
    now += 13;
    a.check(1, 0, now);
    expect(a.alertCount).toBe(2);
    a.check(0, 0, now);
    now += 4.9;
    a.check(0, 0, now);
    expect(a.alertCount).toBe(2);
    now += 0.2;
    a.check(0, 0, now);
    expect(a.alertCount).toBe(0);
    expect(a.volumeMultiplier).toBe(1);
  });

  it('alerts when the face is lost', () => {
    expect(a.check(0, 4.9, now)).toBe(false);
    expect(a.check(0, 5, now)).toBe(true);
    expect(a.lastReason).toBe('faceLost');
  });

  it('can ignore a lost face', () => {
    a.options.faceLostAlert = false;
    expect(a.check(0, 60, now)).toBe(false);
  });

  it('reports ringing only during the sound', () => {
    a.check(1, 0, now);
    expect(a.isRinging(now + 2.9)).toBe(true);
    expect(a.isRinging(now + 3)).toBe(false);
  });

  it('reset clears everything', () => {
    a.check(2, 0, now);
    a.reset();
    expect(a.cooldownRemaining(now)).toBe(0);
    expect(a.check(2, 0, now)).toBe(true);
  });
});

describe('SessionStats', () => {
  let ms: number;
  let s: SessionStats;
  beforeEach(() => {
    ms = Date.UTC(2026, 0, 1, 10, 0, 0);
    s = new SessionStats(() => ms);
  });

  it('records data points with the current alert count', () => {
    s.recordAlert('eyesClosed');
    s.addDataPoint({ ear: 0.123456, eyeState: 'closed', page: 2 });
    expect(s.dataPoints[0]).toEqual({
      timestamp: '2026-01-01T10:00:00.000Z',
      ear: 0.1235,
      eyeState: 'closed',
      page: 2,
      alerts: 1,
    });
  });

  it('summarises the session', () => {
    s.visitPage(1);
    s.visitPage(2);
    s.visitPage(2);
    s.recordAlert('eyesClosed');
    s.recordAlert('faceLost');
    ms += 3_600_000;
    const sum = s.summary();
    expect(sum.pagesVisited).toBe(2);
    expect(sum.readingSpeed).toBeCloseTo(2);
    expect(sum.alerts).toBe(2);
    expect(sum.alertsFaceLost).toBe(1);
  });

  it('always writes a CSV header', () => {
    expect(s.toCsv()).toBe('timestamp,ear,eye_state,page,alerts\n');
  });

  it('exports valid JSON', () => {
    s.addDataPoint({ ear: 0.3, eyeState: 'open', page: 1 });
    const data = JSON.parse(s.toJson());
    expect(data.dataPoints).toHaveLength(1);
    expect(data.session.start).toBe('2026-01-01T10:00:00.000Z');
  });
});
