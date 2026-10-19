@echo off
setlocal
cd /d "%~dp0"
if not exist "%~dp0.venv\Scripts\python.exe" (
  echo Run Setup.bat first to restore the local Python environment.
  pause
  exit /b 1
)
"%~dp0.venv\Scripts\python.exe" "%~dp0context_menu.py" uninstall
pause
