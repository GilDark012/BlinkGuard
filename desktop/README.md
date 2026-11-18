# BlinkGuard: Desktop v1 (PyQt6)

> **Status: feature-frozen.** This is version 1 of BlinkGuard. It gets bug fixes only. New features go into the web app.
> The interface of this version is in French.

A desktop PDF reader that watches your eyes through the webcam and rings an alarm when they stay closed.

## Features

- **Real-time eye tracking** (about 30 FPS): MediaPipe Face Mesh and the Eye Aspect Ratio (EAR) tell open eyes from closed ones.
- **Progressive alarm**: a 5 s sound, then a 10 s pause. Each new alert is 20% louder, up to 3×.
- **Face-lost alarm**: rings if your face leaves the camera for 5 s (for example, when your head drops).
- **Built-in PDF reader**: buttons or arrow keys / PageUp / PageDown to turn pages, zoom from 50% to 300%.
- **Statistics**: reading time, pages visited, blinks, alerts, attention score. Export to CSV or JSON.

## Requirements

- Python 3.9–3.12 (MediaPipe does not support newer versions yet)
- A webcam
- Audio output

## Installation

```bash
cd desktop

# 1. Create a Python 3.11 virtual environment in a path WITHOUT accents
#    (MediaPipe cannot load its models when the path contains é, è, ...)
py -3.11 -m venv C:\venvs\blinkguard          # Windows
C:\venvs\blinkguard\Scripts\activate

# 2. Install the pinned dependencies
pip install -r requirements.txt

# 3. Run the app
python main.py
```

> ⚠️ Use a dedicated environment. A recent `protobuf`, pulled in by other packages
> (Streamlit, TensorBoard, ...), breaks MediaPipe 0.10.x.

## Using the app

The window has two panels:

- **Left: eye tracking.** The webcam view with live annotations, a Start/Stop button, the EAR, the eye state, the blink count, how long the eyes have been closed, and the alert status and cooldown.
- **Right: PDF reader.** The document, a zoom slider, Previous/Next buttons, and reading statistics.

### Keyboard shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+O` | Open a PDF |
| `Ctrl+S` | Show statistics |
| `Ctrl+Q` | Quit |
| `→` / `PageDown` | Next page |
| `←` / `PageUp` | Previous page |

### Settings

Settings live in [`config.py`](config.py):

| Setting | Meaning |
|---|---|
| `ear_threshold` | Closed-eye sensitivity (lower means less sensitive) |
| `trigger_seconds` | How long the eyes must stay closed before an alert |
| `duration` / `cooldown` | Length of the alarm and the pause before it can ring again |
| `face_lost_alert` / `face_lost_seconds` | Alarm when the face disappears |
| `webcam_index` | Which camera to use |

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest
```

The tests cover the alert state machine, the eye-state logic, the PDF reader and the statistics exports. They use a fake clock and need no webcam or audio.

## Troubleshooting

**Webcam not detected**

```bash
python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

On Linux, check that your user can access `/dev/video0`.

**No sound**

```bash
python -c "import pygame; pygame.mixer.init(); print('OK')"
```

If audio cannot start, the app shows a warning and keeps running without sound.

## Architecture

```
desktop/
├── main.py                    # PyQt6 window, timers, dialogs
├── config.py                  # All settings
├── core/
│   ├── eye_tracker.py         # MediaPipe Face Mesh, EAR, eye state
│   ├── alert_system.py        # Alert state machine and sound
│   ├── pdf_reader.py          # PDF rendering and reading time (PyMuPDF)
│   └── statistics_manager.py  # Session statistics, CSV/JSON export
├── tests/                     # pytest suite
└── exports/                   # Default folder for exports
```

## Privacy

- Everything is processed on your machine.
- No video is recorded or sent anywhere.
- Exports are saved locally only.
