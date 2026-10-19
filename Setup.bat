@echo off
setlocal
cd /d "%~dp0"
echo Prism - first-time setup
where py >nul 2>nul
if errorlevel 1 goto no_python
py -3.12 --version >nul 2>nul
if errorlevel 1 goto no_python
if not exist ".venv\Scripts\python.exe" py -3.12 -m venv .venv
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
echo.
echo Ready. Double-click Start-Prism.bat to open Prism.
pause
exit /b 0
:no_python
echo Install Python 3.12 for Windows from https://www.python.org/downloads/windows/
echo Include the Python launcher during installation, then run Setup.bat again.
pause
exit /b 1
:failed
echo Setup failed. Check the error above and your internet connection.
pause
exit /b 1
