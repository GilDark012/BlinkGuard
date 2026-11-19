import { ALERT_CONFIG, EYE_CONFIG, PDF_CONFIG, STATS_CONFIG } from './config';
import { AlertSystem } from './core/alertSystem';
import type { Point } from './core/ear';
import { EyeStateTracker } from './core/eyeState';
import { SessionStats } from './core/stats';
import { initLang, LANGS, onLangChange, setLang, t, type Lang } from './i18n';
import { Alarm } from './services/alarm';
import { CameraError, startCamera, stopCamera } from './services/camera';
import { FaceTracker } from './services/faceTracker';
import { PdfViewer } from './services/pdfViewer';

// ------------------------------------------------------------------ DOM

const $ = <T extends HTMLElement>(id: string): T => {
  const el = document.getElementById(id);
  if (!el) throw new Error(`Missing #${id}`);
  return el as T;
};

const ui = {
  video: $<HTMLVideoElement>('video'),
  overlay: $<HTMLCanvasElement>('overlay'),
  camPlaceholder: $('cam-placeholder'),
  camPlaceholderText: $('cam-placeholder-text'),
  statePill: $('state-pill'),
  toggle: $<HTMLButtonElement>('toggle-tracking'),
  camError: $('cam-error'),
  ear: $('m-ear'),
  blinks: $('m-blinks'),
  closed: $('m-closed'),
  alerts: $('m-alerts'),
  intensity: $('m-intensity'),
  cooldown: $('m-cooldown'),
  testSound: $<HTMLButtonElement>('test-sound'),
  mute: $<HTMLButtonElement>('mute'),
  audioWarning: $('audio-warning'),
  banner: $('alarm-banner'),
  sDuration: $('s-duration'),
  sPages: $('s-pages'),
  sSpeed: $('s-speed'),
  sBlinkRate: $('s-blink-rate'),
  sAlerts: $('s-alerts'),
  exportCsv: $<HTMLButtonElement>('export-csv'),
  exportJson: $<HTMLButtonElement>('export-json'),
  resetStats: $<HTMLButtonElement>('reset-stats'),
  openPdf: $<HTMLButtonElement>('open-pdf'),
  fileInput: $<HTMLInputElement>('file-input'),
  prev: $<HTMLButtonElement>('prev-page'),
  next: $<HTMLButtonElement>('next-page'),
  pageLabel: $('page-label'),
  zoomOut: $<HTMLButtonElement>('zoom-out'),
  zoomIn: $<HTMLButtonElement>('zoom-in'),
  zoomLabel: $('zoom-label'),
  stage: $('pdf-stage'),
  pdfEmpty: $('pdf-empty'),
  pdfError: $('pdf-error'),
  pdfCanvas: $<HTMLCanvasElement>('pdf-canvas'),
  privacyLink: $<HTMLButtonElement>('privacy-link'),
  dialog: $<HTMLDialogElement>('privacy-dialog'),
  privacyAccept: $<HTMLButtonElement>('privacy-accept'),
  privacyCancel: $<HTMLButtonElement>('privacy-cancel'),
};

// ------------------------------------------------------------------ state

const eyes = new EyeStateTracker(EYE_CONFIG.earThreshold);
const alerts = new AlertSystem({ ...ALERT_CONFIG });
const stats = new SessionStats();
const alarm = new Alarm();
const pdf = new PdfViewer(ui.pdfCanvas);

let tracker: FaceTracker | null = null;
let stream: MediaStream | null = null;
let tracking = false;
let starting = false;
let privacyAccepted = false;
let lastVideoTime = -1;
let lastUiUpdate = 0;
let dataTimer: number | undefined;

const seconds = () => performance.now() / 1000;

// ------------------------------------------------------------------ eye tracking

async function startTracking(): Promise<void> {
  if (tracking || starting) return;
  starting = true;
  hideError(ui.camError);
  renderToggle();
  try {
    await alarm.unlock(); // we are inside the click: browsers allow audio now
    ui.camPlaceholderText.textContent = t('cam.loading');
    if (!tracker) {
      try {
        tracker = await FaceTracker.create();
      } catch (e) {
        throw new CameraError('err.model', e instanceof Error ? e.message : String(e));
      }
    }
    stream = await startCamera(ui.video);
    ui.overlay.width = ui.video.videoWidth;
    ui.overlay.height = ui.video.videoHeight;
    ui.camPlaceholder.hidden = true;

    tracking = true;
    eyes.start(seconds());
    alerts.reset();
    lastVideoTime = -1;
    dataTimer = window.setInterval(recordDataPoint, STATS_CONFIG.dataPointIntervalMs);
    requestAnimationFrame(loop);
  } catch (e) {
    stopCamera(ui.video, stream);
    stream = null;
    ui.camPlaceholderText.textContent = t('cam.off');
    const err = e instanceof CameraError ? e : new CameraError('err.cameraGeneric', String(e));
    showError(ui.camError, t(err.messageKey, { detail: err.detail }));
  } finally {
    starting = false;
    renderToggle();
    renderAudioWarning();
  }
}

function stopTracking(): void {
  if (!tracking) return;
  tracking = false;
  window.clearInterval(dataTimer);
  stopCamera(ui.video, stream);
  stream = null;
  eyes.stop();
  alerts.reset();
  alarm.stop();
  setRinging(false);
  ui.overlay.getContext('2d')?.clearRect(0, 0, ui.overlay.width, ui.overlay.height);
  ui.camPlaceholder.hidden = false;
  ui.camPlaceholderText.textContent = t('cam.off');
  renderToggle();
  renderTracking(seconds());
}

function loop(): void {
  if (!tracking || !tracker) return;
  const now = seconds();

  // Only analyse new video frames.
  if (ui.video.readyState >= 2 && ui.video.currentTime !== lastVideoTime) {
    lastVideoTime = ui.video.currentTime;
    const reading = tracker.detect(ui.video, performance.now());
    if (eyes.update(reading?.ear ?? null, now)) stats.blinks += 1;
    drawOverlay(reading?.left, reading?.right);
  }

  if (alerts.check(eyes.closedSeconds(now), eyes.faceMissingSeconds(now), now)) {
    alarm.play(alerts.volumeMultiplier, ALERT_CONFIG.duration, ALERT_CONFIG.frequency);
    if (alerts.lastReason) stats.recordAlert(alerts.lastReason);
    renderAudioWarning();
  }
  setRinging(alerts.isRinging(now));

  if (now - lastUiUpdate > 0.1) {
    lastUiUpdate = now;
    renderTracking(now);
  }
  requestAnimationFrame(loop);
}

function drawOverlay(left?: Point[], right?: Point[]): void {
  const ctx = ui.overlay.getContext('2d');
  if (!ctx) return;
  ctx.clearRect(0, 0, ui.overlay.width, ui.overlay.height);
  const color = eyes.state === 'closed' ? '#f97316' : '#22c55e';
  for (const eye of [left, right]) {
    if (!eye?.length) continue;
    const xs = eye.map((p) => p.x);
    const ys = eye.map((p) => p.y);
    const pad = 10;
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.strokeRect(Math.min(...xs) - pad, Math.min(...ys) - pad,
      Math.max(...xs) - Math.min(...xs) + 2 * pad, Math.max(...ys) - Math.min(...ys) + 2 * pad);
    ctx.fillStyle = '#facc15';
    for (const p of eye) {
      ctx.beginPath();
      ctx.arc(p.x, p.y, 2.5, 0, Math.PI * 2);
      ctx.fill();
    }
  }
}

function recordDataPoint(): void {
  if (!tracking) return;
  stats.addDataPoint({ ear: eyes.ear, eyeState: eyes.state, page: pdf.loaded ? pdf.page : 0 });
}

let ringing = false;
function setRinging(value: boolean): void {
  if (value === ringing) return;
  ringing = value;
  document.body.classList.toggle('ringing', value);
  ui.banner.hidden = !value;
  if (value) ui.banner.textContent = t(alerts.lastReason === 'faceLost' ? 'alarm.faceLost' : 'alarm.eyesClosed');
}

// The page stops getting frames while hidden: forget timers so we don't
// raise an alarm for time we could not observe.
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible') eyes.clearTimers();
});

// ------------------------------------------------------------------ PDF

async function openFile(file: File): Promise<void> {
  hideError(ui.pdfError);
  try {
    await pdf.load(await file.arrayBuffer());
    ui.pdfEmpty.hidden = true;
    ui.pdfCanvas.hidden = false;
    stats.visitPage(pdf.page);
  } catch {
    showError(ui.pdfError, t('pdf.error'));
  }
  renderPdf();
}

async function goTo(page: number): Promise<void> {
  if (await pdf.goTo(page)) {
    stats.visitPage(pdf.page);
    ui.stage.scrollTop = 0;
  }
  renderPdf();
}

async function zoomBy(delta: number): Promise<void> {
  if (!pdf.loaded) return;
  await pdf.setZoom(pdf.zoom + delta);
  renderPdf();
}

// ------------------------------------------------------------------ rendering

function renderToggle(): void {
  ui.toggle.disabled = starting;
  ui.toggle.textContent = starting ? t('cam.loading') : t(tracking ? 'cam.stop' : 'cam.start');
  ui.toggle.classList.toggle('stop', tracking);
}

let lastState = '';
function renderTracking(now: number): void {
  if (eyes.state !== lastState) {
    lastState = eyes.state;
    ui.statePill.dataset.state = eyes.state;
    ui.statePill.textContent = t(`state.${eyes.state}`);
  }
  ui.ear.textContent = tracking ? eyes.ear.toFixed(3) : '–';
  ui.blinks.textContent = String(eyes.blinks);
  ui.closed.textContent = `${eyes.closedSeconds(now).toFixed(1)} s`;
  ui.alerts.textContent = String(alerts.alertCount);
  ui.intensity.textContent = `${Math.round(alerts.volumeMultiplier * 100)}%`;
  const cooldown = alerts.cooldownRemaining(now);
  ui.cooldown.textContent = cooldown > 0 ? `${cooldown.toFixed(1)} s` : '–';
}

function renderStats(): void {
  const s = stats.summary();
  const total = Math.floor(s.durationSeconds);
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const sec = String(total % 60).padStart(2, '0');
  ui.sDuration.textContent = h ? `${h}:${String(m).padStart(2, '0')}:${sec}` : `${m}:${sec}`;
  ui.sPages.textContent = String(s.pagesVisited);
  ui.sSpeed.textContent = s.durationSeconds >= 60 ? s.readingSpeed.toFixed(1) : '–';
  ui.sBlinkRate.textContent = tracking ? eyes.blinkRate(seconds()).toFixed(1) : '–';
  ui.sAlerts.textContent = String(s.alerts);
}

function renderPdf(): void {
  const loaded = pdf.loaded;
  ui.pageLabel.textContent = loaded ? t('pdf.page', { current: pdf.page, total: pdf.total }) : '';
  ui.zoomLabel.textContent = t('pdf.zoomLevel', { percent: Math.round(pdf.zoom * 100) });
  ui.prev.disabled = !loaded || pdf.page <= 1;
  ui.next.disabled = !loaded || pdf.page >= pdf.total;
  ui.zoomOut.disabled = !loaded || pdf.zoom <= PDF_CONFIG.minZoom;
  ui.zoomIn.disabled = !loaded || pdf.zoom >= PDF_CONFIG.maxZoom;
}

function renderMute(): void {
  ui.mute.setAttribute('aria-pressed', String(alarm.muted));
  ui.mute.textContent = t(alarm.muted ? 'alarm.soundOff' : 'alarm.soundOn');
}

function renderAudioWarning(): void {
  ui.audioWarning.hidden = !(tracking && alarm.blocked && !alarm.muted);
}

function renderLangButtons(lang: Lang): void {
  document.querySelectorAll<HTMLButtonElement>('[data-lang]').forEach((b) => {
    b.setAttribute('aria-pressed', String(b.dataset.lang === lang));
  });
}

function renderAll(): void {
  lastState = '';
  renderToggle();
  renderTracking(seconds());
  renderStats();
  renderPdf();
  renderMute();
  if (!tracking && !starting) ui.camPlaceholderText.textContent = t('cam.off');
  if (ringing) ui.banner.textContent = t(alerts.lastReason === 'faceLost' ? 'alarm.faceLost' : 'alarm.eyesClosed');
}

function showError(el: HTMLElement, message: string): void {
  el.textContent = message;
  el.hidden = false;
}

function hideError(el: HTMLElement): void {
  el.hidden = true;
  el.textContent = '';
}

// ------------------------------------------------------------------ export

function download(content: string, type: string, extension: string): void {
  const stamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-');
  const url = URL.createObjectURL(new Blob([content], { type }));
  const a = document.createElement('a');
  a.href = url;
  a.download = `blinkguard-session-${stamp}.${extension}`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 0);
}

// ------------------------------------------------------------------ events

function openPrivacy(withCamera: boolean): void {
  ui.privacyAccept.hidden = !withCamera;
  ui.privacyCancel.textContent = t(withCamera ? 'privacy.cancel' : 'privacy.close');
  ui.dialog.showModal();
}

ui.toggle.addEventListener('click', () => {
  if (tracking) stopTracking();
  else if (privacyAccepted) void startTracking();
  else openPrivacy(true);
});

ui.privacyAccept.addEventListener('click', () => {
  privacyAccepted = true;
  ui.dialog.close();
  void startTracking();
});
ui.privacyCancel.addEventListener('click', () => ui.dialog.close());
ui.privacyLink.addEventListener('click', () => openPrivacy(false));

ui.testSound.addEventListener('click', async () => {
  await alarm.unlock();
  const wasMuted = alarm.muted;
  alarm.muted = false;
  alarm.play(1, 1.5, ALERT_CONFIG.frequency);
  alarm.muted = wasMuted;
  renderAudioWarning();
});

ui.mute.addEventListener('click', () => {
  alarm.muted = !alarm.muted;
  if (alarm.muted) alarm.stop();
  renderMute();
  renderAudioWarning();
});

// Any click can unlock audio that the browser suspended.
document.addEventListener('pointerdown', () => {
  if (alarm.blocked) void alarm.unlock().then(renderAudioWarning);
});

ui.exportCsv.addEventListener('click', () => download(stats.toCsv(), 'text/csv', 'csv'));
ui.exportJson.addEventListener('click', () => download(stats.toJson(), 'application/json', 'json'));
ui.resetStats.addEventListener('click', () => {
  stats.reset();
  if (pdf.loaded) stats.visitPage(pdf.page);
  renderStats();
});

ui.openPdf.addEventListener('click', () => ui.fileInput.click());
ui.fileInput.addEventListener('change', () => {
  const file = ui.fileInput.files?.[0];
  if (file) void openFile(file);
  ui.fileInput.value = '';
});
ui.prev.addEventListener('click', () => void goTo(pdf.page - 1));
ui.next.addEventListener('click', () => void goTo(pdf.page + 1));
ui.zoomOut.addEventListener('click', () => void zoomBy(-PDF_CONFIG.zoomStep));
ui.zoomIn.addEventListener('click', () => void zoomBy(PDF_CONFIG.zoomStep));

ui.stage.addEventListener('dragover', (e) => {
  e.preventDefault();
  ui.stage.classList.add('dragging');
});
ui.stage.addEventListener('dragleave', () => ui.stage.classList.remove('dragging'));
ui.stage.addEventListener('drop', (e) => {
  e.preventDefault();
  ui.stage.classList.remove('dragging');
  const file = e.dataTransfer?.files[0];
  if (file) void openFile(file);
});

document.addEventListener('keydown', (e) => {
  if (e.ctrlKey || e.metaKey || e.altKey || ui.dialog.open) return;
  const target = e.target as HTMLElement;
  if (target.closest('input, textarea, select')) return;
  switch (e.key) {
    case 'ArrowRight':
    case 'PageDown':
      e.preventDefault();
      void goTo(pdf.page + 1);
      break;
    case 'ArrowLeft':
    case 'PageUp':
      e.preventDefault();
      void goTo(pdf.page - 1);
      break;
    case '+':
    case '=':
      void zoomBy(PDF_CONFIG.zoomStep);
      break;
    case '-':
      void zoomBy(-PDF_CONFIG.zoomStep);
      break;
    case 'o':
    case 'O':
      ui.fileInput.click();
      break;
  }
});

document.querySelectorAll<HTMLButtonElement>('[data-lang]').forEach((b) => {
  b.addEventListener('click', () => {
    const lang = b.dataset.lang as Lang;
    if (LANGS.includes(lang)) setLang(lang);
  });
});

window.addEventListener('pagehide', () => {
  stopTracking();
  tracker?.close();
});

// ------------------------------------------------------------------ start

onLangChange((lang) => {
  renderLangButtons(lang);
  renderAll();
});
initLang();
setInterval(renderStats, 1000);
