# BlinkGuard — No Break Reading

A PDF reader that watches your eyes through the webcam and wakes you up with a sound alarm when you fall asleep or close your eyes while reading.

Final project for the *Human Machine Interface* course (Aivancity, PGE-5).

## How it works

- **Eye tracking**: MediaPipe Face Mesh finds the eye landmarks and computes the **Eye Aspect Ratio (EAR)**. When the EAR stays below a threshold for N consecutive frames, the eyes count as closed.
- **Alerts**: an alarm rings for 3 s, then waits through a 10 s cooldown. If the eyes stay closed, each new alert is 20% louder than the last one.
- **PDF reader**: open a PDF, move between pages, and zoom from 50% to 300%.
- **Statistics**: reading time, pages visited, blinks, an attention score, and export to CSV or JSON.

## Repository layout

| Path | Description |
|------|-------------|
| [`no_break_reading_pyqt/`](no_break_reading_pyqt/) | **Main app**: PyQt6 desktop version |
| [`no_break_reading/`](no_break_reading/) | Earlier Streamlit web version |
| [`eye_track.py`](eye_track.py) | Standalone prototype: detects open or closed eyes |
| [`eye_song.py`](eye_song.py) | Standalone prototype: eye detection plus a sound alert |
| [`No Break Reader conversation perplexity.md`](No%20Break%20Reader%20conversation%20perplexity.md) | Development log (the design conversation) |

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
