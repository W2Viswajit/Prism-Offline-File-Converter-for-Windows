@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run Setup.bat first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m pip install --only-binary=:all: -r requirements-ocr.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip check
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -c "from rapidocr import RapidOCR; import onnxruntime; print('OCR imports OK')"
if errorlevel 1 goto failed
echo OCR installed. Quit Prism from its tray icon, then restart it.
pause
exit /b 0
:failed
echo OCR installation failed. Base conversion tools are still available.
pause
exit /b 1
