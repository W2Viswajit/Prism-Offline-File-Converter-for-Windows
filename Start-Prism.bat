@echo off
setlocal
cd /d "%~dp0"
if not exist "%~dp0.venv\Scripts\python.exe" (
  echo Prism setup is missing. Run Setup.bat first.
  pause
  exit /b 1
)
echo Opening Prism. Keep this window open while using the app.
echo If startup fails, the error will remain visible here.
"%~dp0.venv\Scripts\python.exe" "%~dp0main.py" %*
if errorlevel 1 (
  echo.
  echo Prism exited with an error. Copy the error above or send a screenshot.
  echo A startup log may also be in %%LOCALAPPDATA%%\Prism\logs\startup.log
  pause
)
