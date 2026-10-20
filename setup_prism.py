"""Visible, logged setup; invoked by Setup.bat with an available Python."""
import platform
import struct
import subprocess
import sys
import sysconfig
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def compatible():
    return (sys.version_info[:2] in ((3, 12), (3, 13))
            and not sysconfig.get_config_var('Py_GIL_DISABLED')
            and struct.calcsize('P') == 8
            and platform.machine().lower() in ('amd64', 'x86_64'))

def main():
    if '--check' in sys.argv:
        return 0 if compatible() else 1
    if not compatible():
        print('Use standard 64-bit x64 Python 3.12 or 3.13 (including 3.13.3).')
        return 1
    log_path = ROOT / 'setup.log'
    with log_path.open('w', encoding='utf-8') as log:
        def say(message):
            print(message, flush=True)
            log.write(message + '\n'); log.flush()
        def run(args):
            say('Running: ' + subprocess.list2cmdline(list(map(str, args))))
            with subprocess.Popen(list(map(str, args)), cwd=ROOT,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  text=True, encoding='utf-8', errors='replace') as proc:
                for line in proc.stdout:
                    say(line.rstrip())
                if proc.wait():
                    raise RuntimeError('Command failed; see the error above.')
        try:
            say('Prism setup using ' + sys.version.split()[0] + ' at ' + sys.executable)
            python = ROOT / '.venv' / 'Scripts' / 'python.exe'
            if python.exists():
                run([python, ROOT / 'setup_prism.py', '--check'])
            else:
                run([sys.executable, '-m', 'venv', ROOT / '.venv'])
            run([python, '-m', 'pip', 'install', '--upgrade', 'pip'])
            run([python, '-m', 'pip', 'install', '--only-binary=:all:', '-r', ROOT / 'requirements.txt'])
            run([python, '-m', 'pip', 'check'])
            run([python, '-c', 'import PySide6.QtWidgets, PIL, pypdf, pypdfium2, reportlab, win32com.client; import prism.ui; print("Prism imports OK")'])
            say('Ready. Open Start-Prism.bat. For the Explorer entry, run Install-Right-Click.bat.')
            return 0
        except (OSError, RuntimeError) as exc:
            say('SETUP FAILED: ' + str(exc))
            say('Log saved to: ' + str(log_path))
            say('If an old environment is broken, extract this ZIP into a NEW folder and retry.')
            return 1

if __name__ == '__main__':
    sys.exit(main())
