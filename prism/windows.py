"""Exclusive native shortcut and bounded Explorer drag observation."""
import sys,ctypes
from ctypes import wintypes
from PySide6.QtCore import QObject,QTimer,Signal,QAbstractNativeEventFilter
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QApplication

def left_button_down():
    if sys.platform=='win32':return bool(ctypes.windll.user32.GetAsyncKeyState(1)&0x8000)
    from PySide6.QtCore import Qt
    return bool(QApplication.mouseButtons() & Qt.LeftButton)

class HotkeyFilter(QAbstractNativeEventFilter):
    def __init__(self,bridge):super().__init__();self.bridge=bridge
    def nativeEventFilter(self,event_type,message):
        if bytes(event_type) in (b'windows_generic_MSG',b'windows_dispatcher_MSG'):
            msg=wintypes.MSG.from_address(int(message))
            if msg.message==0x0312 and msg.wParam==self.bridge.hotkey_id and self.bridge.registered:
                self.bridge.queue_shortcut();return True,0
        return False,0

class ExplorerBridge(QObject):
    requested=Signal(list,bool)
    hotkey_id=0x5052
    def __init__(self,parent=None):
        super().__init__(parent);self.start=None;self.shown=False;self._enabled=False
        self._busy=False;self._pending=False;self.registered=False;self.filter=None
        self.timer=QTimer(self);self.timer.timeout.connect(self.poll)
        if sys.platform=='win32':
            self.user=ctypes.windll.user32;self.user.GetForegroundWindow.restype=wintypes.HWND
            self.filter=HotkeyFilter(self);QApplication.instance().installNativeEventFilter(self.filter)
            QApplication.instance().aboutToQuit.connect(self.close)
            self.timer.start(40)
        self.enabled=True
    @property
    def enabled(self):return self._enabled
    @enabled.setter
    def enabled(self,value):
        self._enabled=bool(value)
        if sys.platform!='win32':return
        if value and not self.registered:
            # MOD_ALT | MOD_CONTROL | MOD_NOREPEAT. Windows consumes this chord;
            # foreground Explorer never also handles it as a separate action.
            self.registered=bool(self.user.RegisterHotKey(None,self.hotkey_id,0x4003,0x20))
        elif not value and self.registered:
            self.user.UnregisterHotKey(None,self.hotkey_id);self.registered=False
    def close(self):
        self.enabled=False;self.timer.stop()
        if self.filter is not None:
            QApplication.instance().removeNativeEventFilter(self.filter);self.filter=None
    def queue_shortcut(self):
        if not self.enabled or self._pending or self._busy:return
        self._pending=True
        QTimer.singleShot(0,self.activate_shortcut)
    def activate_shortcut(self):
        if not self.enabled:self._pending=False;return
        self._busy=True
        try:self.requested.emit(self.selected(),False)
        finally:self._busy=False;self._pending=False
    def selected(self):
        try:
            hwnd=int(self.user.GetForegroundWindow() or 0)
            name=ctypes.create_unicode_buffer(256);self.user.GetClassNameW(wintypes.HWND(hwnd),name,256)
            if name.value not in ('CabinetWClass','ExploreWClass'):return []
            import win32com.client
            shell=win32com.client.Dispatch('Shell.Application')
            for window in shell.Windows():
                try:
                    if int(window.HWND)==hwnd:
                        return [str(item.Path) for item in window.Document.SelectedItems() if not item.IsFolder]
                except Exception:continue
        except Exception:pass
        return []
    def poll(self):
        if not self.enabled or self._busy:return
        if not left_button_down():self.start=None;self.shown=False;return
        point=QCursor.pos()
        if self.start is None:self.start=point;self.shown=False
        if self.shown or not (self.user.GetAsyncKeyState(0x10)&0x8000) or (point-self.start).manhattanLength()<=14:return
        # Latch before COM: Shell calls may pump this timer's events recursively.
        self.shown=True;self._busy=True
        try:
            paths=self.selected()
            if paths and left_button_down():self.requested.emit(paths,True)
        finally:self._busy=False
