"""Windows-native geometry/input checks at a caller-selected Qt scale factor."""
import ctypes,json,os,sys
from ctypes import wintypes
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication,QWidget
from PySide6.QtCore import QPoint,QTimer,Qt
from prism.widgets import Wheel
from prism.theme import appearance,stylesheet
app=QApplication([]); background=QWidget(); background.resize(700,600); background.show()
w=Wheel(); results=[]
def check():
    try:
        for choice in ('Light','Dark'):
            t=appearance(choice); app.setStyleSheet(stylesheet(t)); w.theme=t
            w.present([('a','One'),('_tools','Tools'),('_back','Back')],choice)
            w.move(background.mapToGlobal(QPoint(50,50))); app.processEvents()
            user=ctypes.windll.user32; user.WindowFromPoint.argtypes=[wintypes.POINT]; user.WindowFromPoint.restype=wintypes.HWND
            class RECT(ctypes.Structure): _fields_=[('left',ctypes.c_long),('top',ctypes.c_long),('right',ctypes.c_long),('bottom',ctypes.c_long)]
            rect=RECT(); user.GetWindowRect(wintypes.HWND(int(w.winId())),ctypes.byref(rect))
            corner=user.WindowFromPoint(wintypes.POINT(rect.left+2,rect.top+2))
            center=user.WindowFromPoint(wintypes.POINT((rect.left+rect.right)//2,(rect.top+rect.bottom)//2))
            assert corner!=int(w.winId()), 'Invisible corner intercepted native hit testing'
            assert center==int(w.winId()), 'Center did not receive native hit testing'
            im=w.grab().toImage(); assert im.pixelColor(0,0).alpha()==0
            assert any(0<im.pixelColor(x,im.height()//2).alpha()<255 for x in range(im.width()//8)), 'Missing antialiasing'
            results.append({'theme':choice,'dpr':w.devicePixelRatioF(),'corner_passes_through':True,'center_hits_wheel':True,'antialiased_edge':True})
        print(json.dumps(results),flush=True)
    finally: w.hide(); background.hide(); app.quit()
QTimer.singleShot(500,check); app.exec()
