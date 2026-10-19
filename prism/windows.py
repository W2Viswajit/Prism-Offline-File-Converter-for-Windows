"""Windows Explorer integration; no keyboard capture, injection or clipboard polling."""
import sys, ctypes
from ctypes import wintypes
from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtGui import QCursor

def apply_backdrop(widget):
    if sys.platform!='win32': return False
    # Documented DWM system backdrop: 3 = desktop acrylic, 2 = mica.
    try:
        dwm=ctypes.windll.dwmapi
        hwnd=wintypes.HWND(int(widget.winId()))
        dark=ctypes.c_int(1); material=ctypes.c_int(3)
        dwm.DwmSetWindowAttribute(hwnd,20,ctypes.byref(dark),4)
        return dwm.DwmSetWindowAttribute(hwnd,38,ctypes.byref(material),4)==0
    except Exception: return False

class ExplorerBridge(QObject):
    requested=Signal(list,bool)
    def __init__(self,parent=None):
        super().__init__(parent); self.last_hot=False; self.start=None; self.shown=False; self.enabled=True
        self.timer=QTimer(self); self.timer.timeout.connect(self.poll)
        if sys.platform=='win32':
            self.user=ctypes.windll.user32
            self.user.GetForegroundWindow.restype=wintypes.HWND
            self.timer.start(60)
    def selected(self):
        try:
            import win32com.client
            hwnd=int(self.user.GetForegroundWindow() or 0)
            shell=win32com.client.Dispatch('Shell.Application')
            for window in shell.Windows():
                try:
                    if int(window.HWND)==hwnd:
                        return [str(item.Path) for item in window.Document.SelectedItems() if not item.IsFolder]
                except Exception: continue
        except Exception: pass
        return []
    def poll(self):
        if not self.enabled: return
        down=lambda key: bool(self.user.GetAsyncKeyState(key)&0x8000)
        hot=down(0x11) and down(0x12) and down(0x20)
        if hot and not self.last_hot: self.requested.emit(self.selected(),False)
        self.last_hot=hot
        if down(1):
            point=QCursor.pos()
            if self.start is None: self.start=point; self.shown=False
            if not self.shown and down(0x10) and (point-self.start).manhattanLength()>14:
                paths=self.selected()
                if paths:
                    self.shown=True; self.requested.emit(paths,True)
        else: self.start=None; self.shown=False
