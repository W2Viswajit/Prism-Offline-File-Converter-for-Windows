"""Compact controls with stable hover metrics and a single file-selection outline."""
from pathlib import Path
from PySide6.QtCore import Qt,QSize,QRectF,QEvent,Signal
from PySide6.QtGui import QPainter,QPen,QColor,QPixmap,QIcon,QFont
from PySide6.QtWidgets import QStyledItemDelegate,QStyle,QPushButton,QVBoxLayout,QLabel
from .theme import appearance,tint

def line_icon(kind,color,size=20):
    pix=QPixmap(size,size); pix.fill(Qt.transparent)
    p=QPainter(pix); p.setRenderHint(QPainter.Antialiasing); p.scale(size/24,size/24)
    p.setPen(QPen(QColor(color),1.5,Qt.SolidLine,Qt.RoundCap,Qt.RoundJoin))
    p.setBrush(Qt.NoBrush)
    if kind=='crop':
        p.drawLine(7,3,7,17); p.drawLine(7,17,21,17); p.drawLine(3,7,17,7); p.drawLine(17,7,17,21)
    elif kind=='resize':
        for a,b,c,d in [(5,5,10,5),(5,5,5,10),(5,5,10,10),(19,19,14,19),(19,19,19,14),(19,19,14,14)]:p.drawLine(a,b,c,d)
    elif kind=='compress_image':
        for x,y,dx,dy in [(4,4,1,1),(20,4,-1,1),(4,20,1,-1),(20,20,-1,-1)]:
            p.drawLine(x,y,x+5*dx,y+5*dy); p.drawLine(x+5*dx,y+5*dy,x+5*dx,y+dy);p.drawLine(x+5*dx,y+5*dy,x+dx,y+5*dy)
    elif kind=='ocr':
        for x,y,dx,dy in [(4,4,1,1),(20,4,-1,1),(4,20,1,-1),(20,20,-1,-1)]:p.drawLine(x,y,x+4*dx,y);p.drawLine(x,y,x,y+4*dy)
        p.drawLine(8,9,16,9);p.drawLine(12,9,12,16)
    elif kind in ('rotate_image','rotate_pdf','history'):
        p.drawArc(QRectF(5,5,14,14),35*16,285*16);p.drawLine(19,4,19,9);p.drawLine(19,9,14,9)
        if kind=='history':p.drawLine(12,8,12,12);p.drawLine(12,12,15,14)
    elif kind=='settings':
        for y,x in [(6,9),(12,16),(18,7)]:p.drawLine(3,y,21,y);p.setBrush(QColor(color));p.drawEllipse(x-2,y-2,4,4);p.setBrush(Qt.NoBrush)
    elif kind=='brand':
        p.drawEllipse(3,3,18,18)
        for a,b,c,d in [(3,12,15,12),(9,4,15,15),(20,7,14,18),(20,17,9,17),(10,21,5,10)]:p.drawLine(a,b,c,d)
    else:
        p.drawRoundedRect(QRectF(6,3,13,18),2,2);p.drawLine(9,9,16,9);p.drawLine(9,13,16,13)
    p.end();return QIcon(pix)

class ToolButton(QPushButton):
    def __init__(self,key,label,parent=None):
        super().__init__(parent); self.key=key; self.setObjectName('tool'); self.setAccessibleName(label)
        self.setProperty('action',key); self.setMinimumHeight(62)
        layout=QVBoxLayout(self);layout.setContentsMargins(12,8,12,8);layout.setSpacing(4)
        self.symbol=QLabel();self.symbol.setAlignment(Qt.AlignCenter)
        self.caption=QLabel(label);self.caption.setAlignment(Qt.AlignCenter)
        for widget in (self.symbol,self.caption):
            widget.setAttribute(Qt.WA_TransparentForMouseEvents);layout.addWidget(widget)
        self.refresh(appearance())
    def refresh(self,t): self.symbol.setPixmap(line_icon(self.key,t.text,18).pixmap(18,18))

class FileDelegate(QStyledItemDelegate):
    def __init__(self,view): super().__init__(view);self.view=view
    def sizeHint(self,option,index):return QSize(200,62)
    def paint(self,painter,option,index):
        t=getattr(self.view,'theme',None) or appearance();r=option.rect.adjusted(0,3,-1,-3)
        selected=bool(option.state & QStyle.State_Selected);hover=bool(option.state & QStyle.State_MouseOver)
        painter.save();painter.setRenderHint(QPainter.Antialiasing)
        surface=t.accent if selected and t.high_contrast else tint(t.surface,t.accent,.10 if selected else .05 if hover else 0)
        painter.setBrush(QColor(surface));painter.setPen(QPen(QColor(t.accent if selected else surface),1))
        painter.drawRoundedRect(QRectF(r).adjusted(.5,.5,-.5,-.5),8,8)
        text=t.accent_text if selected and t.high_contrast else t.text
        line_icon('file',t.accent if not t.high_contrast else text,18).paint(painter,r.left()+13,r.center().y()-9,18,18)
        path=Path(index.data(Qt.UserRole));left=r.left()+42;width=max(1,r.width()-90)
        font=QFont(option.font);font.setBold(True);painter.setFont(font);painter.setPen(QColor(text))
        name=painter.fontMetrics().elidedText(path.name,Qt.ElideMiddle,width)
        painter.drawText(r.adjusted(42,7,-48,-26),Qt.AlignVCenter|Qt.AlignLeft,name)
        font.setBold(False);font.setPointSizeF(max(8,font.pointSizeF()-1));painter.setFont(font)
        painter.setPen(QColor(text if t.high_contrast else t.muted))
        meta=index.data(Qt.UserRole+1) or ''
        painter.drawText(r.adjusted(42,29,-48,-6),Qt.AlignVCenter|Qt.AlignLeft,painter.fontMetrics().elidedText(meta,Qt.ElideRight,width))
        x=r.right()-20;y=r.center().y();painter.setPen(QPen(QColor(t.muted),1.5));painter.drawLine(x-4,y-4,x+4,y+4);painter.drawLine(x-4,y+4,x+4,y-4)
        painter.restore()
    def editorEvent(self,event,model,option,index):
        if event.type()==QEvent.MouseButtonRelease and event.button()==Qt.LeftButton and event.position().x()>option.rect.right()-40:
            self.view.remove_requested.emit(index.data(Qt.UserRole));return True
        return super().editorEvent(event,model,option,index)
