"""Bootstrap diagnostics before importing Qt so pythonw failures are visible."""
import sys
import os
import traceback
from pathlib import Path
from datetime import datetime

def log_path():
    root=Path(os.environ.get('LOCALAPPDATA',str(Path.home()))) / 'Prism' / 'logs'
    root.mkdir(parents=True,exist_ok=True)
    return root / 'startup.log'

def report_error(message,path):
    text=f'Prism could not start.\n\n{message}\n\nDetails: {path}\n\nPlease include this log when reporting the problem.'
    if sys.platform=='win32':
        import ctypes
        ctypes.windll.user32.MessageBoxW(None,text,'Prism startup error',0x10)
    else:
        print(text,file=sys.__stderr__)

def launch():
    try:
        path=log_path()
        stream=path.open('a',encoding='utf-8',buffering=1)
    except OSError:
        path=Path(__file__).resolve().parent / 'startup.log'
        stream=path.open('a',encoding='utf-8',buffering=1)
    # pythonw supplies None for standard streams. Give imports and native Qt
    # diagnostics a real destination rather than losing their error messages.
    if sys.stdout is None: sys.stdout=stream
    if sys.stderr is None: sys.stderr=stream
    print(f'\n{datetime.now().isoformat()} Starting Prism; Python {sys.version}; executable {sys.executable}',file=stream)
    def handle_exception(kind,value,tb):
        traceback.print_exception(kind,value,tb,file=stream)
        if sys.__stderr__ is not None: traceback.print_exception(kind,value,tb,file=sys.__stderr__)
        report_error(str(value),path)
    sys.excepthook=handle_exception
    try:
        from prism.ui import main
        print('Application modules imported. Initializing GUI.',file=stream)
        main()
    except SystemExit:
        raise
    except Exception as e:
        handle_exception(type(e),e,e.__traceback__)
        raise SystemExit(1)

if __name__=='__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    if len(sys.argv)==4 and sys.argv[1]=='--verify-installation':
        from prism.diagnostics import verify
        raise SystemExit(verify(sys.argv[2],sys.argv[3]))
    launch()
