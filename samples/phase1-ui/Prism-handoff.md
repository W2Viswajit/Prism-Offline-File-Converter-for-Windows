# Prism Phase 1 handoff — 20 October 2026

Implemented directly in `C:\VSCode\Prism-Offline-File-Converter-for-Windows`.

## What changed

- `prism/widgets.py`: removed the acrylic backdrop; isolated the wheel's stylesheet; clear-alpha painting and a circular native input region preserve antialiased edges and transparent corners. Submenus update in place, with Back/Backspace, Escape, stopped dismissal timers, and monitor-work-area clamping. Drag-triggered menus now disappear on mouse-button release, checked every 60 ms, rather than lingering for 20 seconds. A menu opened normally retains its existing inactivity timeout.
- `prism/windows.py`: removed the rectangular DWM backdrop and added the mouse-button-state query used to end drag previews.
- `prism/theme.py` (new): shared Windows app-mode, accent, surface tint, text, selection and border tokens. System follows Windows light/dark; explicit Light/Dark remain available and still use the device accent. Personalization is checked every second. High-contrast uses Windows system colors. The wheel uses solid surfaces and no animation, including when reduced effects are requested; its outside area always remains transparent.
- `prism/ui.py`: shared live theme refresh, single-wheel Tools/Back navigation, wheel dismissal when closing the main window, and native Word wording in the DOCX flow. Defaults to System for new settings; existing explicit preferences are preserved.
- `prism/instance.py` (new): per-user process lock plus local IPC. A repeated launch forwards paths to the existing window. Windows named pipes alone did not prevent duplicates; the lock fixes the reproduced issue.
- `prism/engine.py`: rotating selected PDF pages now retains all other pages. PDF render resources are released on failure. DOCX prefers installed Microsoft Word and falls back to LibreOffice when Word is absent. Word runs in an isolated helper, opens the source read-only with macros disabled, has a two-minute export timeout and bounded cleanup of its dedicated instance. Pre-existing Word processes are not forcibly terminated. Output still goes through validated, exclusive, non-overwriting creation.
- `main.py`: multiprocessing bootstrap support for Word's helper, including future frozen builds.
- Added `tests/test_phase1.py`, `tests/native_probe.py`, `tests/verify_samples.py`, `tests/verify_word.py`, and `tests/live_demo.py`.

No sharing, audio, video, installer publication, or account purchases were added.

## Verified

| Check | Evidence / result |
|---|---|
| Regression suite | 37 passed on Windows, Python 3.13.3 / PySide6 6.8.3, with `QT_QPA_PLATFORM=windows` explicitly selected. |
| Wheel corners and edges | Native Windows `WindowFromPoint` excludes corners, includes the center; zero-alpha corner pixels and partially transparent antialiased edge pixels verified in Light and Dark. |
| Scaling | Native probes passed at actual Qt device-pixel ratios 1.0, 1.25 and 1.5. This used `QT_SCALE_FACTOR`, not changes to Windows display settings. |
| Single wheel | Same native window handle and position through Tools/Back; one visible wheel; Escape dismisses it and stops timers. |
| Drag/drop | Qt URL-drop events and selection tested. Drag release dismisses the wheel; a normally opened wheel is not dismissed merely because the mouse button is up. |
| Device accent | Actual Windows accent appeared in the UI. Shared refresh and high-contrast token propagation tested with simulated preference changes. |
| Repeated launch | Two real launches left one main Prism window; the second PDF appeared in its file list. |
| Images | PNG, JPEG, WebP, resize, crop, rotate, compress and images-to-PDF produced readable results. Lossless/alpha and original-preservation checks passed. |
| PDF | Merge, organize/reorder, split, selective rotation, page rendering and embedded-text extraction verified. All output PDF pages rendered and visually reviewed. |
| OCR | Image and scanned-PDF OCR succeeded; the existing OCR test also passed with network connections blocked. |
| Microsoft Word | Word 2016 exported a two-page DOCX with table and page break. PDF producer confirms Microsoft Word; page count/text/rendering verified; source SHA-256 unchanged. |
| Live preview | 18 real jobs ran in the replayable native Qt demonstration, with 18 saved preview captures and output files. The harness supplies fixed options; it is not a claim that every production dialog was clicked manually. |
| Safety | Existing sample SHA-256 hashes unchanged; naming-collision tests passed. |

The full suite initially encountered a test-temp-directory permission conflict in an elevated run. The final run used an explicit workspace test-temp directory and passed. A Word automation hang was reproduced and addressed by isolating export and bounding dedicated-instance cleanup.

## Samples and previews

In the repository:

- `samples\phase1-20261020-175147\index.html`: browsable verified conversion outputs, every PDF page preview, timings and links.
- `samples\live-demo-20261020-180953\`: all 18 live demonstrations, `results.json`, generated outputs and numbered `*-live-preview.png` captures.
- `samples\word-demo-20261020-180818\`: Microsoft Word fixture, resulting PDF, two rendered page previews and verification results.
- `samples\phase1-ui\`: before/after Windows screenshots and this handoff.

The chat's `outputs` folder also contains copies of the verified gallery, live demonstrations and Word result for convenient viewing.

## Launch and replay

In PowerShell:

```powershell
Set-Location 'C:\VSCode\Prism-Offline-File-Converter-for-Windows'
.\.venv\Scripts\pythonw.exe .\main.py
```

The final app was opened with the sample Word document ready to convert. An already running older Prism process must be quit through its tray menu before code changes take effect.

Replay all 18 real jobs:

```powershell
.\.venv\Scripts\pythonw.exe .\tests\live_demo.py
```

The demonstration uses sample inputs and creates another timestamped folder under `samples`. Use its dropdown and **Run selected tool** to replay an individual tool. Word and PDF-OCR entries are included when their generated sample inputs exist.

Run tests:

```powershell
$env:QT_QPA_PLATFORM='windows'
.\.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider
```

## Remaining manual acceptance checks

1. In Prism settings choose **System**. Change Windows Settings > Personalization > Colors between light/dark and several accent colors. Verify both surfaces update within about one second. Explicit Light/Dark should retain their chosen brightness while the accent still follows Windows.
2. Enable a Windows contrast theme, and disable animation/transparency effects. Check actual OS-level transitions; token propagation was tested, but these settings were not changed on your behalf.
3. Move Explorer across physical monitors using different display scales. Invoke the wheel at each screen edge and near the taskbar. Native scale-factor probes passed, but mixed-monitor transitions remain unverified.
4. Select an image in Explorer; try Ctrl+Alt+Space and Shift-drag. Release over empty desktop and verify the wheel disappears promptly. Drop onto a conversion wedge and verify the new output. Synthetic Qt drops and native hit-testing passed; the complete Explorer drag gesture still needs your check.
5. If desired, run `Install-Right-Click.bat`, then right-click one supported file > Show more options > Open with Prism. Registry-command unit tests and real command-line forwarding passed; the Explorer context-menu click was not verified and integration was not installed during this work.
6. In the main app, select a PDF and check Organize pages, Back, Escape and repeated Open wheel activation. Test your own representative documents and fonts. LibreOffice fallback was retained but cannot be integration-tested here because LibreOffice is absent.

Word export requires a functioning installed Word license. Startup/activation or protected-document prompts can still prevent export and will be reported. The tested Word installation needed bounded automation cleanup; the export itself and the final live Word replay succeeded. Very complex documents, missing fonts, linked content and protected files require separate acceptance testing.

## Phase 2 — proposed next release, not implemented

**Recommended initial delivery:** PyInstaller one-folder Windows x64 build wrapped by an Inno Setup EXE installer. The installed app includes Python, Qt, conversion libraries and tested optional OCR assets, so end users need neither Python nor BAT files. One-folder packaging is easier to diagnose and avoids the extraction work of one-file startup. Build and validate on Windows. [PyInstaller packaging guidance](https://pyinstaller.org/en/stable/operating-mode.html).

The installer should provide a Start-menu shortcut, optional desktop shortcut, optional per-user Explorer integration, versioned upgrades, and an entry in Windows Installed apps. Uninstall should remove only Prism-owned binaries, shortcuts and registry entries; preserve user files and generated outputs. Inno tasks support optional shortcuts, while registry cleanup must be explicitly authored. [Inno tasks](https://jrsoftware.org/ishelp/topic_taskssection.htm), [registry cleanup](https://jrsoftware.org/ishelp/topic_registrysection.htm).

Microsoft Word remains an external licensed dependency for native DOCX layout. Do not bundle Word. Decide whether the LibreOffice fallback remains an external prerequisite or becomes a separately installed optional component after size, redistribution and maintenance review. Audit third-party/OCR model licensing, bundle fonts only with appropriate rights, and test offline installation.

| Channel | Proposed approach |
|---|---|
| Direct download | Publish a signed installer on an HTTPS product page with version, SHA-256, release notes and rollback/upgrade instructions. You control hosting, downloads and release cadence. |
| Microsoft Store | Start by assessing Store submission of the same signed Win32 EXE/MSI; alternatively evaluate MSIX for Store-managed package distribution and updates. MSIX requires a separate compatibility pass for Explorer integration, local IPC and Word automation. Store certification and publisher identity are additional steps. |

Microsoft distinguishes signing requirements for Store MSI/EXE installers from MSIX packages that it re-signs after certification. Do not assume the Store route removes signing needs for the existing EXE installer. [Microsoft publishing/signing guidance](https://learn.microsoft.com/windows/apps/package-and-deploy/publish-first-app), [Store onboarding](https://learn.microsoft.com/en-us/windows/apps/publish/get-started).

Your involvement will be needed for the legal publisher name, individual/company account choice and identity verification, signing-provider enrollment and budget, domain/download hosting, public support contact/privacy policy, and final approval of installer defaults and distribution. Verify current account availability and fees during enrollment rather than budgeting from old assumptions. [Partner Center registration](https://learn.microsoft.com/en-us/windows/apps/publish/partner-center/open-a-developer-account).

Before release, test clean Windows 11 VMs without Python; standard-user install/update/uninstall; Unicode paths; offline operation; no-Office/Word/LibreOffice cases; OCR present/absent; locked files and disk-full errors; Defender/SmartScreen reputation; signed upgrades; multi-monitor DPI; high contrast; keyboard-only operation; and original preservation. Confirm frozen multiprocessing and pywin32/ONNX/PDFium collection.

The product webpage should include a concise offline-conversion pitch, supported formats and limitations, real light/dark screenshots, system requirements, installer and optional OCR/Word prerequisites, a usage guide for every tool and Explorer gestures, troubleshooting, release notes, publisher/support/privacy details, and the signed download link with version/hash. Keep the download unpublished until the installer and clean-machine tests pass. No website, Store submission, certificate or account purchase was published or initiated.
