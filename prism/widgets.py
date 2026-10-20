import math
from PySide6.QtCore import Qt,QRectF,QPointF,QPoint,QPropertyAnimation,QEasingCurve,Signal,QTimer
from PySide6.QtGui import QColor,QPainter,QPainterPath,QPen,QFont,QPixmap,QCursor,QRegion
from PySide6.QtWidgets import QWidget,QDialog,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QRubberBand,QDialogButtonBox,QListWidget,QAbstractItemView,QSplitter
from PIL.ImageQt import ImageQt
from .engine import load_image,reader
from .theme import appearance
from .windows import left_button_down

class Wheel(QWidget):
    chosen=Signal(str)
    dropped=Signal(list)
    def __init__(self,parent=None):
        super().__init__(None,Qt.Tool|Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground); self.setAutoFillBackground(False)
        self.setObjectName("prismWheel"); self.setWindowTitle("Prism wheel"); self.setStyleSheet("QWidget#prismWheel { background:transparent; border:0; }")
        self.setFocusPolicy(Qt.StrongFocus)
        # Keep the native input region outside the antialiased paint edge.
        self.setMask(QRegion(14,14,392,392,QRegion.Ellipse))
        self.theme=appearance(); self.scale=1.0
        self.setAcceptDrops(True); self.setMouseTracking(True); self.setFixedSize(420,420)
        self.light=False; self.actions=[]; self.hover=-1; self.title=''; self.drag_mode=False
        self.drag_watch=QTimer(self); self.drag_watch.setInterval(60); self.drag_watch.timeout.connect(self.check_drag_release)
        self.timeout=QTimer(self); self.timeout.setSingleShot(True); self.timeout.timeout.connect(self.hide)
    def present(self,actions,title,drag=False,reposition=True):
        self.actions=actions[:8]; self.title=title; self.hover=-1; self.drag_mode=drag
        from PySide6.QtWidgets import QApplication
        if reposition:
            point=QCursor.pos(); screen=(QApplication.screenAt(point) or QApplication.primaryScreen()).availableGeometry()
            side=min(420,screen.width(),screen.height()); self.scale=side/420
            self.setFixedSize(side,side)
            self.setMask(QRegion(round(14*self.scale),round(14*self.scale),round(392*self.scale),round(392*self.scale),QRegion.Ellipse))
            self.move(max(screen.left(),min(point.x()-side//2,screen.right()-side+1)),max(screen.top(),min(point.y()-side//2,screen.bottom()-side+1)))
        self.setAttribute(Qt.WA_ShowWithoutActivating,drag)
        self.show(); self.raise_()
        if drag: self.timeout.stop(); self.drag_watch.start()
        else: self.drag_watch.stop(); self.timeout.start(20000)
        # No native backdrop or opacity animation: Windows layered alpha keeps
        # the antialiased perimeter and zero-alpha pixels genuinely transparent.
        if not drag: self.activateWindow(); self.setFocus()
        self.update()
    def check_drag_release(self):
        if self.drag_mode and not left_button_down(): self.hide()
    def hideEvent(self,event):
        self.timeout.stop(); self.drag_watch.stop()
        super().hideEvent(event)
    def choose(self,index):
        if not 0<=index<len(self.actions): return
        key=self.actions[index][0]
        if not key.startswith('_'): self.hide()
        self.chosen.emit(key)
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
        return next((i for i in range(len(self.actions)) if self.shape(i).contains(QPointF(pos)/self.scale)),-1)
    def paintEvent(self,event):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        p.setCompositionMode(QPainter.CompositionMode_Source); p.fillRect(self.rect(),Qt.transparent); p.setCompositionMode(QPainter.CompositionMode_SourceOver)
        p.scale(self.scale,self.scale); t=self.theme
        p.setPen(QPen(QColor(t.border),1)); p.setBrush(QColor(t.background)); p.drawEllipse(QRectF(16,16,388,388))
        for i,(key,label) in enumerate(self.actions):
            selected=i==self.hover
            p.setBrush(QColor(t.accent if selected else t.surface)); p.setPen(QPen(QColor(t.accent if selected else t.border),1)); p.drawPath(self.shape(i))
            a=math.radians(90-i*360/len(self.actions)); x=210+128*math.cos(a); y=210-128*math.sin(a)
            p.setPen(QColor(t.accent_text if selected else t.text)); p.setFont(QFont('Segoe UI',11,QFont.DemiBold)); p.drawText(QRectF(x-56,y-30,112,60),Qt.AlignCenter|Qt.TextWordWrap,label)
        p.setPen(QColor(t.text)); p.setFont(QFont('Segoe UI',9,QFont.DemiBold)); p.drawText(QRectF(143,168,134,26),Qt.AlignCenter,'PRISM')
        p.setPen(QColor(t.text)); p.setFont(QFont('Segoe UI',9)); label=self.actions[self.hover][1] if self.hover>=0 else self.title
        p.drawText(QRectF(147,195,126,45),Qt.AlignCenter|Qt.TextWordWrap,label[:36])
        p.setPen(QColor(t.muted)); p.setFont(QFont('Segoe UI',8)); p.drawText(QRectF(147,244,126,20),Qt.AlignCenter,'Esc to close')
    def mouseMoveEvent(self,e): self.hover=self.hit(e.position()); self.update()
    def mouseReleaseEvent(self,e):
        i=self.hit(e.position())
        if i>=0 and e.button()==Qt.LeftButton: self.choose(i)
        else: self.hide()
    def keyPressEvent(self,e):
        if e.key()==Qt.Key_Escape: self.hide()
        elif e.key() in (Qt.Key_Right,Qt.Key_Down): self.hover=(self.hover+1)%max(1,len(self.actions)); self.update()
        elif e.key() in (Qt.Key_Left,Qt.Key_Up): self.hover=(self.hover-1)%max(1,len(self.actions)); self.update()
        elif e.key() in (Qt.Key_Return,Qt.Key_Enter,Qt.Key_Space) and self.hover>=0: self.choose(self.hover)
        elif e.key() in (Qt.Key_Backspace,Qt.Key_Back):
            if any(key=='_back' for key,label in self.actions): self.chosen.emit('_back')
    def dragEnterEvent(self,e):
        if e.mimeData().hasUrls():
            self.drag_mode=True; self.timeout.stop(); self.drag_watch.start()
            e.setDropAction(Qt.CopyAction); e.accept()
    def dragMoveEvent(self,e): self.hover=self.hit(e.position()); self.update(); e.setDropAction(Qt.CopyAction); e.accept()
    def dropEvent(self,e):
        i=self.hit(e.position())
        if i>=0:
            paths=[u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()]
            if paths:
                self.dropped.emit(paths); e.setDropAction(Qt.CopyAction); e.accept(); self.choose(i)
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
        self.show_page(self.items.currentRow())
    def show_page(self,row):
        if row<0: self.preview.clear(); return
        try:
            import pypdfium2 as pdfium
            doc=pdfium.PdfDocument(str(self.path)); page=doc[self.items.item(row).data(Qt.UserRole)]; bm=page.render(scale=min(1,450/page.get_width()))
            pix=QPixmap.fromImage(ImageQt(bm.to_pil())); self.preview.setPixmap(pix.scaled(430,470,Qt.KeepAspectRatio,Qt.SmoothTransformation)); bm.close(); page.close(); doc.close()
        except Exception as e: self.preview.setText(str(e))
    def sequence(self): return ','.join(str(self.items.item(i).data(Qt.UserRole)+1) for i in range(self.items.count()))
