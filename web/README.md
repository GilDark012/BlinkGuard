# BlinkGuard: Web app

The browser version of BlinkGuard. It watches your eyes through the webcam while you read a PDF and rings an alarm when they stay closed. **Everything runs inside the browser tab:** no server, no account, no analytics, and no video or data ever leaves the device.

> Status: in development, run locally only. It is not deployed anywhere yet.

## Run it locally

You need Node.js 20 or newer.

```bash
cd web
npm install
npm run dev        # http://localhost:5173
```

`npm run dev` and `npm run build` first run `scripts/fetch-assets.mjs`. It copies the MediaPipe runtime into `public/mediapipe/` and downloads the face model once from Google's official MediaPipe storage, so the running app never loads code or models from another site.

The camera only works on `localhost` or over HTTPS.

| Command | What it does |
|---|---|
| `npm run dev` | Dev server with hot reload |
| `npm test` | Unit tests (Vitest) |
| `npm run typecheck` | TypeScript check |
| `npm run build` | Production build in `dist/`, with a strict Content-Security-Policy |
| `npm run preview` | Serves the production build on http://localhost:4173 |

## Features

- **Eye tracking** with MediaPipe Face Landmarker (WebAssembly, GPU when available) and the Eye Aspect Ratio.
- **Progressive alarm**, synthesised with the Web Audio API: rings after 1 s of closed eyes or 5 s without a face, waits 10 s, then rings 20% louder each time. The alarm also shows a flashing banner, so it works without sound.
- **PDF reader** with pdf.js: open or drag and drop a file, change page, zoom. The file is read locally.
- **Session statistics**: blinks, alarms, pages visited, pages per hour. Export to CSV or JSON.
- **English and French**, picked from the browser language, with a switch in the top bar.
- **Privacy notice** shown before the camera turns on.
- Keyboard shortcuts, visible focus, screen-reader labels, and reduced motion respected.

## Architecture

```
web/
├── index.html
├── src/
│   ├── main.ts              # Wires the UI, the camera loop and the reader together
│   ├── config.ts            # All settings (same values as desktop v1)
│   ├── core/                # Pure logic, unit-tested, no browser APIs
│   │   ├── ear.ts           # Eye Aspect Ratio
│   │   ├── eyeState.ts      # Open / closed / no face, timed in seconds
│   │   ├── alertSystem.ts   # When to ring and how loud
│   │   └── stats.ts         # Session statistics and CSV/JSON export
│   ├── services/            # Browser APIs
│   │   ├── camera.ts        # getUserMedia with clear error messages
│   │   ├── faceTracker.ts   # MediaPipe Face Landmarker
│   │   ├── alarm.ts         # Web Audio alarm
│   │   └── pdfViewer.ts     # pdf.js rendering
│   └── i18n/                # en.ts, fr.ts and the language switch
└── scripts/fetch-assets.mjs # Self-hosts the MediaPipe runtime and model
```

## Security choices

- Production builds carry a Content-Security-Policy that only allows the app's own origin: no CDN, no inline scripts, no outgoing connections.
- PDFs are untrusted input: pdf.js runs in a worker with `isEvalSupported: false` and XFA disabled.
- The camera is requested only after the privacy notice, video only (never the microphone), and released on Stop or when the page closes.
- Nothing is stored except the language choice in `localStorage`.
