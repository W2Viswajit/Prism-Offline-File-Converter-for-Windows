import os,sys,time
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
from PySide6.QtWidgets import QApplication,QDialog
from PySide6.QtCore import Qt,QPoint
from PySide6.QtTest import QTest
from PIL import Image
from prism.ui import Window,DARK
from prism.widgets import CropDialog,PagesDialog,Wheel

@pytest.fixture(scope='module')
def app():
    a=QApplication.instance() or QApplication([]); a.setStyleSheet(DARK); return a

def test_ui_conversion(app,tmp_path):
    p=tmp_path/'test.png'; Image.new('RGBA',(100,100),(10,20,30,70)).save(p)
    w=Window(); w.add_files([str(p)]); w.show(); app.processEvents()
    assert ('webp','WebP') in w.actions(w.selected())
    w.start('webp')
    deadline=time.monotonic()+10
    while w.job and time.monotonic()<deadline: app.processEvents(); time.sleep(.01)
    assert w.job is None and len(w.outputs)==1 and Path(w.outputs[0]).exists()
    assert w.open_result.isEnabled(); w.quitting=True; w.close()

def test_crop_mapping(app,tmp_path):
    p=tmp_path/'image.png'; Image.new('RGB',(1000,500)).save(p)
    d=CropDialog(str(p),None); d.show(); app.processEvents(); c=d.canvas
    r=c.rect; left=QPoint(round(r.left()+r.width()*.25),round(r.top()+r.height()*.25)); right=QPoint(round(r.left()+r.width()*.75),round(r.top()+r.height()*.75))
    QTest.mousePress(c,Qt.LeftButton,pos=left); QTest.mouseMove(c,right); QTest.mouseRelease(c,Qt.LeftButton,pos=right)
    box=c.box(); assert box is not None
    assert abs(box[0]-250)<4 and abs(box[2]-750)<4
    d.close()

def test_wheel_selection(app):
    w=Wheel(); w.present([('png','PNG'),('jpg','JPG'),('webp','WebP')],'sample.png'); app.processEvents()
    selected=[]; w.chosen.connect(selected.append); QTest.keyClick(w,Qt.Key_Right); QTest.keyClick(w,Qt.Key_Return)
    assert selected==['png']; w.close()

def test_pdf_editor(app,tmp_path):
    from reportlab.pdfgen import canvas
    p=tmp_path/'pages.pdf'; c=canvas.Canvas(str(p))
    for i in range(3):c.drawString(10,10,str(i)); c.showPage()
    c.save(); d=PagesDialog(str(p),None); d.show(); app.processEvents()
    d.items.setCurrentRow(2); d.move(-1); assert d.sequence()=='1,3,2'
    d.remove(); assert d.sequence()=='1,2'; d.close()
