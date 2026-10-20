import sys,ctypes
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication,QPushButton,QStyleOptionButton,QStyle
from PySide6.QtCore import Qt,QPoint,QByteArray
from PySide6.QtTest import QTest
from PIL import Image
from prism.ui import Window
from prism.windows import ExplorerBridge

def dispose(w):
    w.bridge.close();w.theme_timer.stop();w.wheel.close();w.hide()
    if w.tray:w.tray.hide()

def test_reference_layout_hover_and_file_removal(tmp_path):
    app=QApplication.instance() or QApplication([]);app.setStyle('Fusion')
    p=tmp_path/'sample-image.png';Image.new('RGB',(100,80),'red').save(p)
    w=Window();w.bridge.enabled=False
    try:
        w.add_files([str(p)]);w.show();app.processEvents()
        buttons=w.findChildren(QPushButton)
        assert not any(b.text()=='Open wheel' for b in buttons)
        assert any(b.text()=='Convert to PDF' for b in buttons)
        for b in buttons:
            if not b.isVisible() or not b.text():continue
            option=QStyleOptionButton();b.initStyleOption(option)
            before=b.style().subElementRect(QStyle.SE_PushButtonContents,option,b)
            QTest.mouseMove(b,b.rect().center());app.processEvents()
            after_option=QStyleOptionButton();b.initStyleOption(after_option)
            after=b.style().subElementRect(QStyle.SE_PushButtonContents,after_option,b)
            assert before==after, b.text()
            assert b.fontMetrics().horizontalAdvance(b.text())<=after.width(),b.text()
        w.files.setCurrentRow(0);app.processEvents()
        item=w.files.item(0);rect=w.files.visualItemRect(item)
        QTest.mouseClick(w.files.viewport(),Qt.LeftButton,pos=QPoint(rect.right()-20,rect.center().y()))
        assert not w.paths and w.files.count()==0
    finally:dispose(w)

def test_shortcut_coalesces_and_guards_com_reentry(monkeypatch):
    app=QApplication.instance() or QApplication([])
    bridge=ExplorerBridge();bridge.enabled=False;bridge._enabled=True
    calls=[]
    def selected():
        bridge.queue_shortcut() # Simulate COM pumping another key message.
        calls.append('selected');return ['sample.png']
    monkeypatch.setattr(bridge,'selected',selected)
    received=[];bridge.requested.connect(lambda p,d:received.append((p,d)))
    try:
        for _ in range(20):bridge.queue_shortcut()
        app.processEvents()
        assert calls==['selected'] and received==[(['sample.png'],False)]
        assert not bridge._pending and not bridge._busy
    finally:bridge.close()

def test_shortcut_toggles_one_wheel_and_drag_reuses_it(tmp_path,monkeypatch):
    app=QApplication.instance() or QApplication([])
    p=tmp_path/'sample.png';Image.new('RGB',(20,20)).save(p)
    w=Window();w.bridge.enabled=False
    try:
        w.explorer_wheel([str(p)],False);handle=w.wheel.winId();normal=list(w.wheel.actions)
        assert w.wheel.isVisible()
        w.explorer_wheel([],False);assert not w.wheel.isVisible()
        monkeypatch.setattr('prism.widgets.left_button_down',lambda:True)
        w.explorer_wheel([str(p)],True)
        assert w.wheel.winId()==handle and w.wheel.actions==normal and w.wheel.drag_mode
        monkeypatch.setattr('prism.widgets.left_button_down',lambda:False)
        w.wheel.check_drag_release();assert not w.wheel.isVisible()
    finally:dispose(w)
