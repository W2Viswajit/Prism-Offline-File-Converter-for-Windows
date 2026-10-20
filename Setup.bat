@echo off
setlocal
cd /d "%~dp0"
echo Prism - Python 3.12 / 3.13 setup
python "%~dp0setup_prism.py" --check >nul 2>nul
if not errorlevel 1 goto use_python
py -3.13 "%~dp0setup_prism.py" --check >nul 2>nul
if not errorlevel 1 goto use_313
py -3.12 "%~dp0setup_prism.py" --check >nul 2>nul
if not errorlevel 1 goto use_312
echo Could not find compatible 64-bit x64 Python 3.12 or 3.13.
echo If Python 3.13.3 is installed, enable its PATH option or Python launcher.
pause
exit /b 1
:use_python
python -u "%~dp0setup_prism.py"
goto finished
:use_313
py -3.13 -u "%~dp0setup_prism.py"
goto finished
:use_312
py -3.12 -u "%~dp0setup_prism.py"
:finished
set "PRISM_SETUP_EXIT=%errorlevel%"
echo.
echo Setup exit code: %PRISM_SETUP_EXIT%
echo Detailed output is saved in setup.log in this folder.
pause
exit /b %PRISM_SETUP_EXIT%
