# Before 2026-11: the course project

**Context:** final project for the *Human Machine Interface* course (Aivancity, PGE-5), first called *No Break Reading*, then *Wake Reader*, now **BlinkGuard**.

## Goal

A reading aid that notices when the reader's eyes close, for example when falling asleep over a PDF, and wakes them up with a sound.

## Done

1. **Prototype 1** ([`prototypes/eye_track.py`](../../../prototypes/eye_track.py)): MediaPipe Face Mesh plus the Eye Aspect Ratio (EAR) to tell open eyes from closed ones in an OpenCV window.
2. **Prototype 2** ([`prototypes/eye_song.py`](../../../prototypes/eye_song.py)): adds a sound alert after the eyes stay closed, with a cooldown and alarms that get louder each time.
3. **Streamlit version**: a web interface with a PDF viewer and statistics.
4. **PyQt6 version**: a native desktop window with the webcam panel next to a PDF reader, menus, shortcuts and CSV/JSON export. It became the main app and was presented for the course, with a slide deck and a demo video.

## Learned / problems

- EAR is simple and explainable, but the right threshold depends on the person and the lighting.
- Streamlit runs Python on the server, so the webcam and the speaker it uses are the server's, not the visitor's. It cannot work as an online app.
- PDF zoom needed care: rendering at the right scale and keeping the image memory layout valid for Qt.

## Next

Publish the code, review it properly, and turn it into a project that can live online.
