# Changelog

User-facing changes to BlinkGuard. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
The desktop app and the web app are versioned separately (`desktop-vX.Y.Z`, `web-vX.Y.Z`).
For the full story of how the project is built, see the [project journal](docs/journal/README.md).

## [Unreleased]: web app

### Added

- Browser version of BlinkGuard in [`web/`](web/), running entirely on the user's device.
- Eye tracking with MediaPipe Face Landmarker, with the same alarm rules as desktop v1.
- Alarm with sound and a flashing banner, plus a "Test sound" button and a mute toggle.
- PDF reader: open or drag and drop, pages, zoom.
- Session statistics with CSV and JSON export.
- English interface with a French switch.
- Privacy notice shown before the camera starts.

## [desktop-v1.0.0] - 2026-11-18

First tagged version of the PyQt6 desktop app. It is now feature-frozen.

### Added

- Alarm when the face leaves the camera for 5 s.
- Keyboard shortcuts for pages (arrows, Page Up, Page Down).
- "Eyes closed for" timer in the eye-tracking panel.
- Clear error messages when the webcam, the face model or a PDF fails.
- Test suite (33 tests) and continuous integration.

### Changed

- The alarm delay is now measured in seconds, so it no longer depends on the webcam frame rate.
- The alarm sound no longer blocks the window.
- Zoom changes are smoother (debounced re-rendering).
- Dependencies pinned to versions known to work together (MediaPipe 0.10.x needs `protobuf<5`).

### Fixed

- A brief eye opening no longer skips the pause between two alarms.
- Blinks are counted once per closure.
- Exported statistics record the real eye state, and the CSV always has a header.
- Opening an invalid PDF keeps the current document instead of failing.

### Removed

- The Streamlit web version, which could not work online.

[Unreleased]: https://github.com/GilDark012/BlinkGuard/compare/desktop-v1.0.0...HEAD
[desktop-v1.0.0]: https://github.com/GilDark012/BlinkGuard/releases/tag/desktop-v1.0.0
