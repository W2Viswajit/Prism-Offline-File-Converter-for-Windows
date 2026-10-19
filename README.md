# Prism for Windows — v0.1.1 beta

A local desktop file utility built for Viswajit: a Fluent-inspired radial menu,
image conversion and cropping, PDF page tools, text extraction and optional OCR.
No accounts, cloud processing, sharing, video or audio features.

## Start on your Windows 11 laptop

1. Install **64-bit Python 3.12** from https://www.python.org/downloads/windows/.
   Include the Python launcher (`py`) in the installation options.
2. Extract this entire ZIP to a writable folder such as `Documents\Prism`.
   Do not run it from inside the ZIP or from `Program Files`.
3. Double-click **Setup.bat**. Internet is needed once to download dependencies.
4. When setup says Ready, double-click **Start-Prism.bat**. Keep its console open while Prism runs; startup errors now stay visible.
5. Click **Add files**, or drag a sample file into the file list.
6. Click an action or **Open wheel**. Outputs appear beside the source with new
   names. Click **Open result** or **Show output folder**.

Python and dependencies run on your laptop; **Colab, API keys, Docker and a GPU
are not needed**. Subsequent base conversions run offline.

## Try these first

- `samples\sample-image.png`: PNG → lossless WebP; open the result.
- The same image: Crop → drag a rectangle → Save.
- Two images in the list: Create PDF. List order is the PDF order; to control it
  precisely, add one at a time or reorder pages afterward.
- `samples\sample-document.pdf`: Organize pages → move Page 3 above Page 2 → Save.
- The same PDF: Extract text. Review, copy locally, or save a revised copy.
- `samples\sample-text.txt`: Create PDF.
- Optional OCR: run `Install-OCR.bat`, quit/restart Prism, add
  `samples\sample-scan.png`, and choose Extract text (OCR).

## Explorer and wheel

Keep Prism running. In a **File Explorer window**, select supported files and
press **Ctrl+Alt+Space**. This opens the radial menu near your pointer. Arrows
choose actions; Enter applies; Esc dismisses. Tools opens a second image wheel.

**Shift-drag is experimental:** select files in Explorer, start dragging, then
hold Shift. Move from the centre into the desired segment and release. Actual
file drops use a copy action. If the Windows drag loop does not enter the overlay,
use Ctrl+Alt+Space or the app's Open wheel button. No desktop-icon selection,
third-party file manager support or universal global hotkey compatibility is
claimed in this beta. The shortcut is polled; it is not reserved from other apps.

Closing the main window normally leaves Prism in the system tray. Double-click
its tray icon to reopen. Right-click → Quit exits. Settings can change this and
turn off Explorer integration. No autostart is installed. The right-click command launches a new Prism window; quit old instances from the tray when finished.

### Right-click entry (new in v0.1.1)

After Setup, double-click **Install-Right-Click.bat**. This registers an entry for
supported extensions for your Windows user only; administrator rights are not
needed and default file associations are unchanged. Right-click **one** supported
file → **Show more options → Open with Prism**. The file opens in Prism, where
you can choose an action or Open wheel. This is a classic menu entry, not a
modern Windows 11 menu extension.

Keep the extracted folder in its final location. If moved, rerun the menu
installer from the new folder. To undo registration, run
**Remove-Right-Click.bat** before deleting the folder. Explorer may need to be
closed and reopened before the menu refreshes. Menu behavior has not been
verified on a Windows machine here.

## Included operations

| Input | Operations |
|---|---|
| JPG/JPEG, PNG, WebP, BMP, single-frame TIFF | PNG/JPG/WebP export, crop one image, aspect-preserving resize, clockwise rotation, compression, images to PDF, optional OCR |
| PDF | Embedded text extraction, merge, split into single-page files, select/reorder pages, rotate selected pages into a new PDF, PNG page rendering at 72–300 DPI, optional OCR |
| UTF-8 TXT | PDF export with an embedded TrueType font |
| DOCX | PDF via a locally installed LibreOffice |

Select a subset of the list to process only those files. With no highlighted
selection, all files in the list are used. Mixed families require a compatible
subset. PDF page syntax supports `1,3,5-8` and reverse ranges such as `3-1`.
Rotate-pages exports only the requested pages; leave the page field blank to
rotate every page. Page extraction/reordering produces static output; do not use
it to preserve digital signatures or interactive form behavior.

## Optional document conversion

Install LibreOffice from https://www.libreoffice.org/download/download-libreoffice/.
The usual `C:\Program Files\LibreOffice\program\soffice.exe` location is detected,
as is `soffice` on PATH. Prism uses a separate temporary LibreOffice profile.
Word does not need to be installed. Fonts, page breaks and complex layouts can
change; review the result. This integration has not been run on Windows here.

## Optional OCR

`Install-OCR.bat` installs RapidOCR/ONNX Runtime into the app's private environment.
The default bundled recognition models are used. Printed English is the tested
case; accuracy for handwriting, uncommon scripts and complex tables is not
promised. OCR outputs editable UTF-8 text, not a searchable PDF or editable Word.
The source launcher is the supported route for optional OCR in this release.

## Quality and performance

- Original files are never edited. Existing output filenames are never overwritten.
- Temporary conversion output is validated before it is published to a new name.
  Output copying is not crash-atomic: a power failure during the final copy may
  leave a partial new output, but the source remains intact.
- PNG and default WebP exports are lossless for the normalized pixels. JPEG is
  lossy; alpha is flattened onto white. JPEG edits require re-encoding.
- Colour profiles are normalized to sRGB where supported. Image metadata is not
  retained. High-bit-depth/professional colour workflows are outside V1 scope.
- Resize preserves aspect ratio and does not enlarge smaller images. Lossless
  compression may not make a file smaller. No target-size guarantee is made.
- Images-to-PDF embeds full-resolution RGB pixels with a 150-DPI page size;
  transparent areas become white. PDF-to-image rasterizes pages at the chosen DPI.
- One background job runs at a time. Cancel is cooperative between engine steps;
  an active image encode or OCR call must return first. Already completed outputs
  are kept, including on a later batch error.
- 60-megapixel input/editor cap. Multi-frame images and encrypted PDFs are rejected.
- TXT PDF export is for ordinary text; missing glyphs, emoji and complex script
  shaping may not render correctly. Review non-Latin output.

## Appearance

Dark, Light and System themes. A custom rounded radial wheel, compact crop editor,
PDF page previews and a small local result workflow. Windows DWM Acrylic is
requested for the wheel where supported; painted translucent surfaces provide a
fallback. Exact native blur/shape behavior has **not** been validated on Windows.
The screenshots under `previews` show actual Qt renders from the test environment,
not a promise of identical compositor effects. System theme is evaluated when
applied; change it in Settings again after changing the Windows theme.

## Optional executable build

On Windows, after Setup, run **Build-EXE.bat**. It uses PyInstaller and places a
base-app build at `dist\Prism\Prism.exe`. Keep the whole `dist\Prism` folder.
This is a build recipe, not a prebuilt or Windows-tested binary. OCR and LibreOffice
are not bundled. No signing certificate is included. A distributable release
needs Windows packaging validation and dependency-license review.

## Troubleshooting

- Setup cannot find Python: install 64-bit Python **3.12** with the launcher.
- Setup download error: check connectivity, run Setup again; it reuses `.venv`.
- App does not appear: run **Debug-Prism.bat** and copy the displayed error.
- Wheel does not appear: ensure Prism is running, use a File Explorer window,
  select files, and try Ctrl+Alt+Space. The main app always provides a fallback.
- Permission denied on output: move source files to a folder you can write to.
- No PDF text: scanned documents need OCR.
- Close seems to do nothing: Prism is in the system tray; right-click → Quit.
- Remove the app: run Remove-Right-Click.bat if installed, quit Prism and delete its extracted folder. Settings can remain
  under `HKEY_CURRENT_USER\Software\Viswajit\Prism` (Qt's user preferences).

## Verification and limits

See `TEST_REPORT.md`. Automated conversion and offscreen Qt interaction tests ran
on Linux/Python 3.12 with the pinned base dependencies. Windows Explorer, native
blur, `.bat` execution, PyInstaller build and DOCX/LibreOffice integration still
require a Windows smoke test. This is a runnable **first beta**, not a signed,
production-certified installer.

## Developer commands

```powershell
.\.venv\Scripts\python.exe -m pip install pytest
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe main.py
```

Source structure: `prism/engine.py` is conversion logic; `ui.py` is app flow;
`widgets.py` contains the wheel/editors; `windows.py` is Explorer/DWM integration.
This project is a fresh implementation, not a fork of the community Tangerine app.

## Startup diagnosis in v0.1.1

The visible launcher now reports Python errors instead of using a silent launch.
`main.py` logs startup to `%LOCALAPPDATA%\Prism\logs\startup.log`.
A Python exception during a right-click/pythonw launch also shows a Windows
message box. The cause of the initial startup failure on your laptop is still
unknown until we see its error. Native process crashes may require the visible
Debug launcher. First launch and conversion from Explorer remain Windows smoke
tests, not verified fixes to that unknown failure.
