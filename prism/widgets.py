import math
from PySide6.QtCore import Qt,QRectF,QPointF,QPoint,QPropertyAnimation,QEasingCurve,Signal,QTimer
from PySide6.QtGui import QColor,QPainter,QPainterPath,QPen,QFont,QPixmap,QCursor
from PySide6.QtWidgets import QWidget,QDialog,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QRubberBand,QDialogButtonBox,QListWidget,QAbstractItemView,QSplitter
from PIL.ImageQt import ImageQt
from .engine import load_image,reader
from .windows import apply_backdrop

class Wheel(QWidget):
    chosen=Signal(str)
    dropped=Signal(list)
    def __init__(self,parent=None):
        super().__init__(None,Qt.Tool|Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground); self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAcceptDrops(True); self.setMouseTracking(True); self.setFixedSize(420,420)
        self.light=False; self.actions=[]; self.hover=-1; self.title=''; self.drag_mode=False
        self.timeout=QTimer(self); self.timeout.setSingleShot(True); self.timeout.timeout.connect(self.hide)
    def present(self,actions,title,drag=False):
        self.actions=actions[:8]; self.title=title; self.hover=-1; self.drag_mode=drag
        from PySide6.QtWidgets import QApplication
        point=QCursor.pos(); screen=(QApplication.screenAt(point) or QApplication.primaryScreen()).availableGeometry()
        self.move(max(screen.left(),min(point.x()-210,screen.right()-420)),max(screen.top(),min(point.y()-210,screen.bottom()-420)))
        self.show(); apply_backdrop(self); self.raise_(); self.timeout.start(20000)
        self.animation=QPropertyAnimation(self,b'windowOpacity'); self.animation.setDuration(110); self.animation.setStartValue(.2); self.animation.setEndValue(1.0); self.animation.start()
        if not drag: self.activateWindow(); self.setFocus()
        self.update()
    def shape(self,i):
        n=len(self.actions); step=360/max(n,1); start=90-i*step-step/2+2; end=start+step-4
        outer=QRectF(25,25,370,370); inner=QRectF(134,134,152,152)
        def at(radius,angle):
            a=math.radians(angle); return QPointF(210+radius*math.cos(a),210-radius*math.sin(a))
        p=QPainterPath(); p.moveTo(at(185,start+3)); p.arcTo(outer,start+3,step-10)
        p.quadTo(at(185,end),at(177,end)); p.lineTo(at(84,end)); p.quadTo(at(76,end),at(76,end-6))
        p.arcTo(inner,end-6,-step+16); p.quadTo(at(76,start),at(84,start)); p.lineTo(at(177,start))
        p.quadTo(at(185,start),at(185,start+3)); p.closeSubpath()
        return p
    def hit(self,pos):
        return next((i for i in range(len(self.actions)) if self.shape(i).contains(QPointF(pos))),-1)
    def paintEvent(self,event):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor('#394859'),1)); p.setBrush(QColor(231,239,249,245) if self.light else QColor(18,25,35,245)); p.drawEllipse(QRectF(16,16,388,388))
        for i,(key,label) in enumerate(self.actions):
            selected=i==self.hover
            p.setBrush((QColor('#b6d6fb') if self.light else QColor('#366c9e')) if selected else (QColor(245,249,255,235) if self.light else QColor(47,60,76,235))); p.setPen(QPen(QColor('#85c4ff') if selected else QColor('#536071'),1)); p.drawPath(self.shape(i))
            a=math.radians(90-i*360/len(self.actions)); x=210+128*math.cos(a); y=210-128*math.sin(a)
            p.setPen(QColor('#17263b') if self.light else QColor('#ffffff')); p.setFont(QFont('Segoe UI',11,QFont.DemiBold)); p.drawText(QRectF(x-56,y-30,112,60),Qt.AlignCenter|Qt.TextWordWrap,label)
        p.setPen(QColor('#2863a8') if self.light else QColor('#8bc7ff')); p.setFont(QFont('Segoe UI',9,QFont.DemiBold)); p.drawText(QRectF(143,168,134,26),Qt.AlignCenter,'PRISM')
        p.setPen(QColor('#17263b') if self.light else QColor('#ffffff')); p.setFont(QFont('Segoe UI',9)); label=self.actions[self.hover][1] if self.hover>=0 else self.title
        p.drawText(QRectF(147,195,126,45),Qt.AlignCenter|Qt.TextWordWrap,label[:36])
        p.setPen(QColor('#54677f') if self.light else QColor('#9baec2')); p.setFont(QFont('Segoe UI',8)); p.drawText(QRectF(147,244,126,20),Qt.AlignCenter,'Esc to close')
    def mouseMoveEvent(self,e): self.hover=self.hit(e.position()); self.update()
    def mouseReleaseEvent(self,e):
        i=self.hit(e.position())
        if i>=0: self.hide(); self.chosen.emit(self.actions[i][0])
        else: self.hide()
    def keyPressEvent(self,e):
        if e.key()==Qt.Key_Escape: self.hide()
        elif e.key() in (Qt.Key_Right,Qt.Key_Down): self.hover=(self.hover+1)%max(1,len(self.actions)); self.update()
        elif e.key() in (Qt.Key_Left,Qt.Key_Up): self.hover=(self.hover-1)%max(1,len(self.actions)); self.update()
        elif e.key() in (Qt.Key_Return,Qt.Key_Enter) and self.hover>=0: self.hide(); self.chosen.emit(self.actions[self.hover][0])
    def dragEnterEvent(self,e):
        if e.mimeData().hasUrls(): e.setDropAction(Qt.CopyAction); e.accept()
    def dragMoveEvent(self,e): self.hover=self.hit(e.position()); self.update(); e.setDropAction(Qt.CopyAction); e.accept()
    def dropEvent(self,e):
        i=self.hit(e.position()); self.hide()
        if i>=0:
            paths=[u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()]
            self.dropped.emit(paths); e.setDropAction(Qt.CopyAction); e.accept(); self.chosen.emit(self.actions[i][0])
    def focusOutEvent(self,e):
        if not self.drag_mode: self.hide()

class CropCanvas(QWidget):
    def __init__(self,path):
        super().__init__(); self.im=load_image(path); self.pix=QPixmap.fromImage(ImageQt(self.im)); self.setMinimumSize(500,350)
        self.band=QRubberBand(QRubberBand.Rectangle,self); self.origin=None; self.selection=None; self.rect=QRectF()
    def paintEvent(self,event):
        p=QPainter(self); p.fillRect(self.contentsRect(),QColor('#111923'))
        scaled=self.pix.size().scaled(self.size(),Qt.KeepAspectRatio); self.rect=QRectF((self.width()-scaled.width())/2,(self.height()-scaled.height())/2,scaled.width(),scaled.height())
        p.drawPixmap(self.rect.toRect(),self.pix)
    def resizeEvent(self,e):
        self.selection=None; self.band.hide(); super().resizeEvent(e)
    def mousePressEvent(self,e):
        if self.rect.contains(e.position()): self.origin=e.position().toPoint(); self.band.setGeometry(self.origin.x(),self.origin.y(),0,0); self.band.show()
    def mouseMoveEvent(self,e):
        if self.origin is not None:
            pos=e.position(); pos.setX(max(self.rect.left(),min(self.rect.right(),pos.x()))); pos.setY(max(self.rect.top(),min(self.rect.bottom(),pos.y())))
            from PySide6.QtCore import QRect
            self.selection=QRect(self.origin,pos.toPoint()).normalized(); self.band.setGeometry(self.selection)
    def mouseReleaseEvent(self,e): self.origin=None
    def box(self):
        if self.selection is None or self.selection.width()<3 or self.selection.height()<3: return None
        r=self.selection; sx=self.im.width/self.rect.width(); sy=self.im.height/self.rect.height()
        return (max(0,round((r.left()-self.rect.left())*sx)),max(0,round((r.top()-self.rect.top())*sy)),min(self.im.width,round((r.right()-self.rect.left())*sx)),min(self.im.height,round((r.bottom()-self.rect.top())*sy)))

class CropDialog(QDialog):
    def __init__(self,path,parent):
        super().__init__(parent); self.setWindowTitle('Crop image'); self.resize(760,620)
        v=QVBoxLayout(self); v.addWidget(QLabel('Crop image')); v.addWidget(QLabel('Drag a rectangle over the image. A new copy will be saved.'))
        self.canvas=CropCanvas(path); v.addWidget(self.canvas,1)
        self.buttons=QDialogButtonBox(QDialogButtonBox.Cancel|QDialogButtonBox.Save); self.buttons.accepted.connect(self.accept); self.buttons.rejected.connect(self.reject); v.addWidget(self.buttons)

class PagesDialog(QDialog):
    def __init__(self,path,parent):
        super().__init__(parent); self.setWindowTitle('PDF pages'); self.resize(780,620)
        v=QVBoxLayout(self); v.addWidget(QLabel('Select pages • Move to reorder • Remove to exclude'))
        split=QSplitter(); v.addWidget(split,1); self.items=QListWidget(); self.items.setSelectionMode(QAbstractItemView.ExtendedSelection); split.addWidget(self.items)
        self.preview=QLabel('Select a page to preview'); self.preview.setAlignment(Qt.AlignCenter); self.preview.setMinimumWidth(400); split.addWidget(self.preview)
        for i in range(len(reader(path).pages)):
            self.items.addItem(f'Page {i+1}'); self.items.item(i).setData(Qt.UserRole,i)
        self.path=path; self.items.currentRowChanged.connect(self.show_page)
        h=QHBoxLayout(); v.addLayout(h)
        for label,fn in [('Move up',lambda:self.move(-1)),('Move down',lambda:self.move(1)),('Remove selected',self.remove)]:
            b=QPushButton(label); b.clicked.connect(fn); h.addWidget(b)
        h.addStretch(); b=QDialogButtonBox(QDialogButtonBox.Cancel|QDialogButtonBox.Save); b.accepted.connect(self.accept); b.rejected.connect(self.reject); v.addWidget(b)
        self.items.setCurrentRow(0)
    def move(self,delta):
        row=self.items.currentRow(); target=row+delta
        if row>=0 and 0<=target<self.items.count(): item=self.items.takeItem(row); self.items.insertItem(target,item); self.items.setCurrentRow(target)
    def remove(self):
        for i in self.items.selectedItems(): self.items.takeItem(self.items.row(i))
    def show_page(self,row):
        if row<0: self.preview.clear(); return
        try:
            import pypdfium2 as pdfium
            doc=pdfium.PdfDocument(str(self.path)); page=doc[self.items.item(row).data(Qt.UserRole)]; bm=page.render(scale=min(1,450/page.get_width()))
            pix=QPixmap.fromImage(ImageQt(bm.to_pil())); self.preview.setPixmap(pix.scaled(430,470,Qt.KeepAspectRatio,Qt.SmoothTransformation)); bm.close(); page.close(); doc.close()
        except Exception as e: self.preview.setText(str(e))
    def sequence(self): return ','.join(str(self.items.item(i).data(Qt.UserRole)+1) for i in range(self.items.count()))
