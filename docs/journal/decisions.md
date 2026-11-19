# Decision log

Decisions that shape BlinkGuard, newest last. Each one says what was chosen, why, and what it costs.
A decision is only replaced by a newer entry that says so, never edited away.

| # | Date | Decision | Status |
|---|---|---|---|
| D1 | 2026-11-09 | Measure every delay in seconds, not frames | Active |
| D2 | 2026-11-09 | Alert when the face leaves the camera | Active |
| D3 | 2026-11-10 | Keep private working notes and raw media out of the public repository | Active |
| D4 | 2026-11-18 | Blur bystanders in published media | Active |
| D5 | 2026-11-18 | Drop the Streamlit version | Active |
| D6 | 2026-11-18 | Freeze the desktop app as v1 | Active |
| D7 | 2026-11-18 | English UI, French switch as early as possible | Active |
| D8 | 2026-11-18 | Build the web app locally, no deployment yet | Active |
| D9 | 2026-11-19 | All processing in the browser, nothing sent anywhere | Active |
| D10 | 2026-11-19 | Self-host the MediaPipe runtime and model | Active |
| D11 | 2026-11-19 | Keep the EAR method in the web app | Active |
| D12 | 2026-11-19 | No "attention score" in the web app | Active |
| D13 | 2026-11-19 | Plain TypeScript, no UI framework | Active |

---

### D1: Measure every delay in seconds, not frames

- **Why:** the first version counted frames, so "eyes closed for N frames" meant a different time at 10 or 30 FPS, and the alarm timing depended on the webcam.
- **Cost:** the logic needs a clock. It takes an injectable one, which also makes it testable with a fake clock.

### D2: Alert when the face leaves the camera

- **Why:** when someone falls asleep, the head often drops and the face leaves the frame. Then the eyes can't be measured, and the old version simply stopped alerting.
- **Cost:** someone who leaves the desk on purpose gets an alarm after 5 s. Stopping tracking avoids it, and a setting can turn it off.

### D3: Keep private working notes and raw media out of the public repository

- **Why:** the repository is public and serves as a CV project. Working notes, the course slide deck, the raw demo video and zips stay local.
- **Cost:** they are not backed up by Git.

### D4: Blur bystanders in published media

- **Why:** classmates visible in the background of the demo did not choose to be published. Only their regions are blurred, so the demo stays readable.

### D5: Drop the Streamlit version

- **Why:** Streamlit runs Python on the server, so it would use the server's webcam and speaker, not the visitor's. It cannot work online, and it duplicated the core code.

### D6: Freeze the desktop app as v1

- **Why:** maintaining two full apps in two languages (Python and TypeScript) doubles the work. The desktop app is tagged `desktop-v1.0.0` and only gets bug fixes. New features go into the web app.
- **Cost:** the desktop UI stays in French, and it won't get the new features.

### D7: English UI, French switch as early as possible

- **Why:** English reaches more recruiters and users. French matters for the course and the local audience. The switch shipped in the first web version.

### D8: Build the web app locally, no deployment yet

- **Why:** putting a camera-based app online raises regulatory questions (GDPR: face data is biometric data, Art. 9; EU AI Act: wording around "attention"; ePrivacy; accessibility law) and security ones. They should be answered before anything goes live.
- **Next step:** a privacy and security checklist to decide on deployment.

### D9: All processing in the browser, nothing sent anywhere

- **Why:**
  - It is the strongest privacy position: no video, face data or statistics ever leave the device.
  - It removes most of the GDPR burden, since no server processes biometric data.
  - It also removes most of the attack surface, since there is no backend.
- **Cost:**
  - Performance depends on the user's machine.
  - Statistics disappear when the tab closes unless exported.

### D10: Self-host the MediaPipe runtime and model

- **Why:**
  - The app makes no request to Google or a CDN at runtime, so no IP address is leaked to a third party.
  - It works offline once loaded.
  - It allows a strict Content-Security-Policy.
- **Cost:** the app serves the files itself: a 3.7 MB model and about 11 MB of WebAssembly loaded by the browser. A script downloads the model at build time.

### D11: Keep the EAR method in the web app

- **Why:** MediaPipe also offers "blink" blendshape scores. EAR was kept because it matches desktop v1, it is easy to explain, and its tests carried over unchanged.
- **Revisit:** when adding calibration (Phase 3), compare EAR with blendshapes on real sessions.

### D12: No "attention score" in the web app

- **Why:**
  - Scoring a person's attention is sensitive under the EU AI Act, especially in education or work.
  - It also sounds more scientific than it is (100 minus 10 per alert).
  - The app reports facts instead: blinks, alarms, pages, time.

### D13: Plain TypeScript, no UI framework

- **Why:** the UI is one screen with a few controls. A framework would add weight and dependencies without real benefit.
- **Revisit:** if Phase 3 adds several screens (settings, history), reconsider a light framework.
