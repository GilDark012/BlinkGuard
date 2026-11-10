# BlinkGuard — No Break Reading

A PDF reader that watches your eyes through the webcam and wakes you up with a sound alarm when you fall asleep or close your eyes while reading.

Final project for the *Human Machine Interface* course (Aivancity, PGE-5).

## Demo

| Eye-closure detection | Progressive alarm |
|:---:|:---:|
| <img src="docs/demo/1-eye-detection.gif" width="300" alt="The eye contours turn red and the state switches from OUVERT to FERME as soon as the eyes close"> | <img src="docs/demo/2-progressive-alarm.gif" width="300" alt="Eyes kept closed: the alarm rings, waits out its cooldown, then rings again 20% louder"> |
| Face Mesh landmarks + Eye Aspect Ratio, live at 30 FPS | Eyes kept closed: the alarm rings, then rings again 20% louder (sped up ×2) |

**PDF reader**: page navigation, zoom and reading progress

<img src="docs/demo/3-pdf-navigation.gif" width="720" alt="Turning a page in the built-in PDF reader">

**Session statistics**: reading time, blinks, alerts, attention score, CSV/JSON export

<img src="docs/demo/4-session-stats.gif" width="720" alt="The statistics dialog summarising the reading session">

## How it works

- **Eye tracking**: MediaPipe Face Mesh finds the eye landmarks and computes the **Eye Aspect Ratio (EAR)**. When the EAR stays below a threshold for about a second, the eyes count as closed.
- **Alerts**: an alarm rings for 5 s, then waits through a 10 s cooldown. If the eyes stay closed, each new alert is 20% louder than the last one. An alarm also goes off when the face leaves the camera for 5 s.
- **PDF reader**: open a PDF, move between pages, and zoom from 50% to 300%.
- **Statistics**: reading time, pages visited, blinks, an attention score, and export to CSV or JSON.

## Repository layout

| Path | Description |
|------|-------------|
| [`no_break_reading_pyqt/`](no_break_reading_pyqt/) | **Main app**: PyQt6 desktop version |
| [`no_break_reading/`](no_break_reading/) | Earlier Streamlit web version |
| [`eye_track.py`](eye_track.py) | Standalone prototype: detects open or closed eyes |
| [`eye_song.py`](eye_song.py) | Standalone prototype: eye detection plus a sound alert |

## Quick start (PyQt6 app)

```bash
py -3.11 -m venv C:\venvs\blinkguard        # path without accents: MediaPipe needs it
C:\venvs\blinkguard\Scripts\activate
cd no_break_reading_pyqt
pip install -r requirements.txt
python main.py
```

You need Python 3.9–3.12, a webcam and working audio output. Run the tests with `pip install -r requirements-dev.txt` and then `python -m pytest`.

## Privacy

Everything runs on your machine. No video is recorded and nothing is sent online.
