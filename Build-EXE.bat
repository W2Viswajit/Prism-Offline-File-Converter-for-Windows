@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run Setup.bat first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m pip install pyinstaller==6.16.0
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --windowed --onedir --name Prism --collect-all pypdfium2 --collect-all reportlab --collect-all PIL --hidden-import win32com.client main.py
if errorlevel 1 goto failed
echo Build finished. Open dist\Prism\Prism.exe. Keep its accompanying folder intact.
echo This build includes the base app. Run the source launcher for optional OCR.
pause
exit /b 0
:failed
echo Build failed. Keep the error above for troubleshooting.
pause
exit /b 1
