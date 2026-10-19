@echo off
setlocal
cd /d "%~dp0"
echo === Prism startup diagnostics ===
if not exist "%~dp0.venv\Scripts\python.exe" (
  echo The private Python environment is missing. Run Setup.bat first.
  pause
  exit /b 1
)
"%~dp0.venv\Scripts\python.exe" --version
"%~dp0.venv\Scripts\python.exe" -m pip check
"%~dp0.venv\Scripts\python.exe" "%~dp0main.py" %*
echo.
echo Process exit code: %errorlevel%
echo Startup log: %%LOCALAPPDATA%%\Prism\logs\startup.log
pause
