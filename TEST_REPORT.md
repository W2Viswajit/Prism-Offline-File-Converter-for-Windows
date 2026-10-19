# Verification report — 19 October 2026

Environment: Linux, Python 3.12.14, Qt/PySide6 6.8.3 offscreen platform.
Base dependency versions are pinned in requirements.txt.

- 27 automated tests passed: image exports, lossless alpha preservation,
  crop and resize dimensions, image rotation, no overwrites, original hashes,
  PDF merge/page order/rotation/split/render, images-to-PDF, text extraction,
  TXT rendering, invalid ranges, cancellation, validation cleanup, encrypted
  PDF rejection and multi-frame rejection.
- Qt tests ran actual background conversion and verified completion buttons;
  simulated crop selection, keyboard wheel selection, and PDF reorder/remove.
- Optional OCR was installed and run against sample-scan.png. Both printed
  English lines were recovered correctly. One run took 1.16 seconds on this
  environment; this is not a prediction for the user's laptop.
- Main window, radial wheel and crop UI were rendered and visually inspected.
- No Windows device was available. Native Explorer gestures, native Acrylic,
  launcher/builder batch scripts, installed executable and LibreOffice DOCX
  rendering were not end-to-end tested.

Use README's sample walkthrough for the Windows acceptance check.

## v0.1.1 follow-up

- Added a visible console launcher, early startup logging and Python exception
  message boxes for silent pythonw launches.
- Added optional per-user classic context-menu registration and removal.
- Three new registry-adapter tests passed: quoted paths/install/remove,
  missing-setup refusal, and preservation of entries owned by another app.
  These tests use an in-memory registry double; they do not verify Explorer UI.
- All Python files passed compilation. Startup log directory and quoted launch
  command checks passed. The original 27 Qt/engine results above are from v0.1;
  the complete suite was then rerun with the pinned dependencies: all 30 tests passed (27 original plus 3 registry-adapter tests).
- The actual startup error on the user's laptop is not yet available. This
  update improves diagnosis; it does not claim to fix an identified root cause.
- Windows registry behavior and launch still require the user's laptop check.
