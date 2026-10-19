@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run Setup.bat first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m pip install -r requirements-ocr.txt
if errorlevel 1 (
  echo OCR installation failed. Base conversion tools are still available.
) else (
  echo OCR installed. Quit Prism from its tray icon, then restart it.
)
pause
