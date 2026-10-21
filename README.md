# Prism

**Your files, simplified.** A private, offline file converter for Windows 11.

Convert images, work with PDFs, extract text, and turn Word documents into PDFs—all on your computer. No accounts, uploads, or subscriptions.

## Download and install

1. Open [GitHub Releases](https://github.com/W2Viswajit/Prism-Offline-File-Converter-for-Windows/releases).
2. Under **Assets**, download **Prism-0.1.3-Setup-x64.exe**. Choose the installer, not the source-code ZIP.
3. Double-click the installer and follow the setup steps.
4. Open **Prism** from the Windows Start menu.

Already have this project folder? Double-click **Prism-0.1.3-Setup-x64.exe** in its root.

**Requirements:** Windows 11, 64-bit x64. Python is bundled; no Python setup or BAT files are needed. Installation offers optional desktop and Explorer right-click shortcuts.

The installer must be attached to a GitHub Release before it is available online. This beta is unsigned, so Windows may display an unknown-publisher warning. Only install a download you trust.

## How to use

1. Click **Add files**, or drag files into the Files card.
2. Choose a conversion or editing tool.
3. Adjust any options and confirm.
4. Click **Open result** or **Show output folder** when finished.

Outputs are saved beside the original with a new filename. **Your originals are never overwritten.** Select rows to process a subset; with no rows selected, Prism uses all files in the list.

## What you can do

| Files | Tools |
| --- | --- |
| Images | Convert to PNG, JPG or WebP; crop, resize, rotate, compress; create PDFs |
| PDFs | Merge, split, reorder/extract pages, rotate pages, export page images, extract text |
| Scanned images and PDFs | Extract text with offline OCR |
| Text files | Convert UTF-8 text to PDF |
| Word documents | Convert DOCX to PDF through Microsoft Word, or LibreOffice when Word is unavailable |

Image inputs: PNG, JPG/JPEG, WebP, BMP and single-frame TIFF. OCR models are included. Word conversion requires Microsoft Word or LibreOffice installed separately. Review OCR text and document layout before relying on the result. JPEG/lossy compression may reduce quality; PDF editing may invalidate signatures or alter interactive forms.

## Explorer and the radial menu

Keep Prism running, select a supported file in File Explorer, and press **Ctrl + Alt + Space**.

- Use the arrow keys and **Enter**, or click a segment.
- **Tools** and **Back** navigate within the same wheel.
- **Escape** dismisses the wheel; repeating the shortcut toggles it.
- Experimental **Shift + drag** opens the wheel while dragging and dismisses on release.

If you enabled Explorer integration during installation, right-click a supported file → **Show more options → Open with Prism**.

## Appearance and closing

**Settings → System** follows Windows light/dark mode and accent color. You can also choose Light or Dark explicitly. Small windows scroll to keep tools accessible.

Closing Prism normally keeps it in the system tray. Right-click the tray icon → **Quit** to exit completely. This behavior can be changed in Settings.

## Uninstall

Open **Windows Settings → Apps → Installed apps → Prism → Uninstall**. Your source files and converted documents are kept.

## Troubleshooting

- **Word conversion unavailable:** install Microsoft Word or LibreOffice.
- **PDF text is empty:** use OCR for scanned pages.
- **Wheel does not open:** ensure Prism is running, select a file in Explorer, and close any older Prism copies. Another app may own the shortcut; the main window remains available.
- **Cannot save:** choose files in a folder you can write to.
- **Startup problem:** check `%LOCALAPPDATA%\Prism\logs\startup.log`.

[Report an issue](https://github.com/W2Viswajit/Prism-Offline-File-Converter-for-Windows/issues) with your Windows version, steps to reproduce, and any error message. Avoid attaching private documents.

## Development

Requires x64 Python 3.13. From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-ocr.txt pytest
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe -m pytest tests -q
```

`samples/` contains four small example inputs. `tests/` contains regression checks, not generated proof files. See [packaging instructions](packaging/README.md) to build or publish an installer, and [third-party notices](THIRD_PARTY.md) for dependencies.
