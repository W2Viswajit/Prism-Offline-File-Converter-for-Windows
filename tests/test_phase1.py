import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import Qt,QPoint,QMimeData,QUrl
from PySide6.QtGui import QDragEnterEvent,QDropEvent
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from prism.ui import Window
from prism.theme import appearance,contrast_text
from prism.engine import run
from PIL import Image
from pypdf import PdfReader

def test_navigation_alpha_and_drop(tmp_path):
    app=QApplication.instance() or QApplication([])
    source=tmp_path/'source.png'; Image.new('RGB',(32,32),'red').save(source)
    w=Window(); w.bridge.enabled=False
    try:
        for choice in ('Light','Dark'):
            w.wheel.theme=appearance(choice)
            w.show_wheel([str(source)],False); app.processEvents()
            handle=w.wheel.winId(); position=w.wheel.pos()
            image=w.wheel.grab().toImage()
            assert image.pixelColor(0,0).alpha()==0
            assert image.pixelColor(image.width()//2,image.height()//2).alpha()==255
            assert not w.wheel.mask().contains(QPoint(0,0))
            assert w.wheel.mask().contains(QPoint(210,210))
            w.wheel.choose(4); app.processEvents()
            assert w.wheel.winId()==handle and w.wheel.pos()==position
            assert w.wheel.actions[-1][0]=='_back'
            assert len([x for x in app.topLevelWidgets() if x.isVisible() and x.objectName()=='prismWheel'])==1
            QTest.keyClick(w.wheel,Qt.Key_Backspace)
            assert w.wheel.actions[-1][0]=='_tools'
            w.wheel.choose(4); QTest.keyClick(w.wheel,Qt.Key_Escape); app.processEvents()
            assert not w.wheel.isVisible() and not w.wheel.timeout.isActive()
        w.show_wheel([str(source)],True)
        mime=QMimeData(); mime.setUrls([QUrl.fromLocalFile(str(source))])
        enter=QDragEnterEvent(QPoint(210,80),Qt.CopyAction,mime,Qt.LeftButton,Qt.NoModifier)
        QApplication.sendEvent(w.wheel,enter); assert enter.isAccepted()
        chosen=[]; w.wheel.chosen.disconnect(); w.wheel.chosen.connect(chosen.append)
        drop=QDropEvent(QPoint(210,80),Qt.CopyAction,mime,Qt.LeftButton,Qt.NoModifier)
        QApplication.sendEvent(w.wheel,drop)
        assert chosen==['png'] and drop.isAccepted() and not w.wheel.isVisible()
    finally:
        w.bridge.timer.stop(); w.theme_timer.stop(); w.wheel.close(); w.hide()
        if w.tray: w.tray.hide()

def test_partial_rotation_keeps_other_pages(tmp_path):
    from reportlab.pdfgen import canvas
    p=tmp_path/'pages.pdf'; c=canvas.Canvas(str(p))
    for i in range(3): c.drawString(50,700,f'Page {i+1}'); c.showPage()
    c.save(); result=PdfReader(run('rotate_pdf',[p],{'pages':'2'})[0])
    assert len(result.pages)==3
    assert [p.rotation for p in result.pages]==[0,90,0]
    assert ['Page '+str(i+1) in p.extract_text() for i,p in enumerate(result.pages)]==[True]*3

def test_accessible_accent_text():
    assert contrast_text('#ffff00')=='#000000'
    assert contrast_text('#000080')=='#ffffff'

def test_instance_forwards_to_primary(tmp_path,monkeypatch):
    import time
    from prism.instance import Instance
    monkeypatch.setattr('prism.instance.Path.home',lambda:tmp_path)
    app=QApplication.instance() or QApplication([])
    import subprocess
    primary=Instance(); received=[]
    primary.received.connect(received.append)
    child=None
    try:
        assert primary.forward([]) is False
        code="from pathlib import Path; from PySide6.QtWidgets import QApplication; from prism.instance import Instance; Path.home=lambda:Path("+repr(str(tmp_path))+"); app=QApplication([]); instance=Instance(); assert instance.forward(["+repr(str(tmp_path/'file.pdf'))+"])"
        child=subprocess.Popen([sys.executable,'-c',code],cwd=str(Path(__file__).resolve().parents[1]),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        deadline=time.monotonic()+10
        while child.poll() is None and time.monotonic()<deadline:
            app.processEvents(); time.sleep(.01)
        assert child.poll()==0, child.communicate(timeout=1)
        app.processEvents()
        assert received==[[str(tmp_path/'file.pdf')]]
    finally:
        if child and child.poll() is None: child.kill(); child.wait()
        primary.server.close(); primary.lock.unlock()

def test_live_theme_refresh(tmp_path,monkeypatch):
    from dataclasses import replace
    from prism import ui
    app=QApplication.instance() or QApplication([])
    w=Window(); w.bridge.enabled=False
    original=appearance('Light')
    updated=replace(original,accent='#ffff00',accent_text='#000000',high_contrast=True,animations=False,transparency=False)
    try:
        monkeypatch.setattr(ui,'appearance',lambda choice:original)
        w.refresh_theme(); assert w.wheel.theme==original
        monkeypatch.setattr(ui,'appearance',lambda choice:updated)
        w.refresh_theme(); assert w.wheel.theme==updated
        assert '#ffff00' in app.styleSheet()
        assert 'background:transparent' in app.styleSheet()
    finally:
        w.bridge.timer.stop(); w.theme_timer.stop(); w.wheel.close(); w.hide()
        if w.tray:w.tray.hide()

def test_drag_wheel_dismisses_on_mouse_release(monkeypatch):
    from prism import widgets
    app=QApplication.instance() or QApplication([])
    wheel=widgets.Wheel()
    try:
        monkeypatch.setattr(widgets,'left_button_down',lambda:True)
        wheel.present([('png','PNG')],'Drag files',True)
        wheel.check_drag_release(); assert wheel.isVisible()
        assert wheel.drag_watch.isActive() and not wheel.timeout.isActive()
        monkeypatch.setattr(widgets,'left_button_down',lambda:False)
        wheel.check_drag_release()
        assert not wheel.isVisible() and not wheel.drag_watch.isActive()
        wheel.present([('png','PNG')],'Normal menu',False)
        wheel.check_drag_release(); assert wheel.isVisible()
    finally: wheel.close()
