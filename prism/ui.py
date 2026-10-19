import os,sys,traceback,threading,json
from pathlib import Path
from PySide6.QtCore import Qt,QObject,Signal,QRunnable,QThreadPool,QUrl,QSettings,QTimer
from PySide6.QtGui import QIcon,QPixmap,QPainter,QColor,QFont,QDesktopServices,QAction
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QFrame,QFileDialog,QListWidget,QListWidgetItem,QAbstractItemView,QGridLayout,QMessageBox,QInputDialog,QProgressBar,QDialog,QDialogButtonBox,QPlainTextEdit,QSystemTrayIcon,QMenu,QCheckBox,QComboBox)
from .engine import run,IMAGES,SUPPORTED,Cancelled
from .widgets import Wheel,CropDialog,PagesDialog
from .windows import ExplorerBridge

DARK='''
QWidget { background:#151d28; color:#edf3fc; font-family:"Segoe UI"; font-size:13px; }
QMainWindow {background:#101722;}
QLabel {background:transparent;}
QLabel#eyebrow {color:#86baff; font-size:11px; font-weight:600;}
QLabel#title {font-size:30px; font-weight:650;}
QLabel#muted {color:#95a8bf;}
QFrame#card {background:#1c2838; border:1px solid #354459; border-radius:16px;}
QPushButton {background:#253449; border:1px solid #3d4e64; padding:10px 16px; border-radius:8px; text-align:left;}
QPushButton:hover {background:#304862; border-color:#83baff;}
QPushButton:pressed {background:#38608c;}
QPushButton:disabled {color:#718096; background:#202b3a;}
QPushButton#primary {background:#9ac6ff; color:#101d2e; font-weight:600; border:0;}
QListWidget,QPlainTextEdit {background:#111a26; border:1px solid #344156; border-radius:8px; padding:8px;}
QListWidget::item {padding:9px; border-radius:5px;}
QListWidget::item:selected {background:#304b6e;}
QProgressBar {background:#26374d; border:0; border-radius:4px; height:7px; text-align:center;}
QProgressBar::chunk {background:#93c6ff; border-radius:4px;}
QLineEdit,QSpinBox,QComboBox {background:#24344a; border:1px solid #455873; padding:7px; border-radius:5px;}
QMenu {background:#202d3f; border:1px solid #41536b;}
QMenu::item {padding:9px 24px;}
QMenu::item:selected {background:#36567c;}
QCheckBox {spacing:8px;}
'''


LIGHT = DARK
for before, after in {
    '#151d28':'#f3f5f8', '#edf3fc':'#192536', '#101722':'#f5f7fa',
    '#86baff':'#285f9c', '#95a8bf':'#53657b', '#1c2838':'#e8eef5',
    '#354459':'#c5d1df', '#253449':'#f5f8fc', '#3d4e64':'#c2cfdf',
    '#304862':'#deebfa', '#83baff':'#4d88ce', '#38608c':'#c3dbf7',
    '#718096':'#8a96a5', '#202b3a':'#e4e9ef', '#9ac6ff':'#2464aa',
    '#101d2e':'#ffffff', '#111a26':'#ffffff', '#344156':'#c6d1de',
    '#304b6e':'#d3e5fc', '#26374d':'#d6e1ee', '#93c6ff':'#397bc8',
    '#24344a':'#ffffff', '#455873':'#b6c6d9', '#202d3f':'#f4f7fb',
    '#41536b':'#c6d2e0', '#36567c':'#d5e6fb'
}.items(): LIGHT=LIGHT.replace(before,after)

def set_theme(choice):
    app=QApplication.instance()
    dark=choice=='Dark' or (choice=='System' and app.styleHints().colorScheme()==Qt.ColorScheme.Dark)
    app.setStyleSheet(DARK if dark else LIGHT)
    return dark

def icon():
    pix=QPixmap(64,64); pix.fill(Qt.transparent); p=QPainter(pix); p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor('#8fc2ff')); p.setPen(Qt.NoPen); p.drawRoundedRect(3,3,58,58,17,17)
    p.setPen(QColor('#17273e')); p.setFont(QFont('Segoe UI',28,QFont.Bold)); p.drawText(pix.rect(),Qt.AlignCenter,'P'); p.end(); return QIcon(pix)

class Signals(QObject):
    progress=Signal(int,int); success=Signal(list); failure=Signal(str); finished=Signal()
class Job(QRunnable):
    def __init__(self,action,paths,options):
        super().__init__(); self.signals=Signals(); self.cancel=threading.Event(); self.action=action; self.paths=paths; self.options=options
    def run(self):
        try: self.signals.success.emit([str(p) for p in run(self.action,self.paths,self.options,self.cancel,self.signals.progress.emit)])
        except Cancelled as e: self.signals.failure.emit(str(e))
        except Exception as e:
            traceback.print_exc(); self.signals.failure.emit(str(e)+'\nAny completed outputs were kept. Originals are unchanged.')
        finally: self.signals.finished.emit()

class DropList(QListWidget):
    files=Signal(list)
    def __init__(self):
        super().__init__(); self.setAcceptDrops(True); self.setSelectionMode(QAbstractItemView.ExtendedSelection)
    def dragEnterEvent(self,e):
        if e.mimeData().hasUrls(): e.acceptProposedAction()
    def dragMoveEvent(self,e): e.acceptProposedAction()
    def dropEvent(self,e):
        self.files.emit([u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()]); e.setDropAction(Qt.CopyAction); e.accept()

class Window(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle('Prism • Offline file tools'); self.setWindowIcon(icon()); self.resize(980,760); self.setMinimumSize(860,680)
        self.settings=QSettings('Viswajit','Prism'); self.paths=[]; self.outputs=[]; self.job=None; self.wheel_paths=[]; self.wheel=Wheel()
        self.wheel.chosen.connect(self.wheel_action)
        self.wheel.dropped.connect(self.set_wheel_paths)
        self.bridge=ExplorerBridge(self); self.bridge.requested.connect(self.explorer_wheel)
        self.bridge.enabled=self.settings.value('explorer',True,type=bool)
        self.wheel.light=not set_theme(self.settings.value('theme','Dark'))
        self.pool=QThreadPool(self); self.pool.setMaxThreadCount(1)
        root=QWidget(); self.setCentralWidget(root); v=QVBoxLayout(root); v.setContentsMargins(32,26,32,22); v.setSpacing(16)
        top=QHBoxLayout(); v.addLayout(top); titles=QVBoxLayout(); top.addLayout(titles)
        eyebrow=QLabel('P R I S M   /   WINDOWS'); eyebrow.setObjectName('eyebrow'); titles.addWidget(eyebrow)
        title=QLabel('Small actions. Clear results.'); title.setObjectName('title'); titles.addWidget(title)
        sub=QLabel('Convert, crop and work with PDFs. Everything stays on this computer.'); sub.setObjectName('muted'); titles.addWidget(sub)
        top.addStretch(); b=QPushButton('Settings'); b.clicked.connect(self.preferences); top.addWidget(b)
        card=QFrame(); card.setObjectName('card'); cv=QVBoxLayout(card); cv.setContentsMargins(20,16,20,16); v.addWidget(card)
        head=QHBoxLayout(); cv.addLayout(head); label=QLabel('Drop your files here'); label.setStyleSheet('font-size:18px; font-weight:600'); head.addWidget(label); head.addStretch()
        add=QPushButton('+ Add files'); add.setObjectName('primary'); add.clicked.connect(self.pick); head.addWidget(add)
        self.files=DropList(); self.files.setMinimumHeight(115); self.files.files.connect(self.add_files); self.files.itemSelectionChanged.connect(self.rebuild_actions); cv.addWidget(self.files)
        row=QHBoxLayout(); cv.addLayout(row)
        self.selection=QLabel('Images · PDF · TXT · DOCX'); self.selection.setObjectName('muted'); row.addWidget(self.selection); row.addStretch()
        for label,fn in [('Remove',self.remove),('Clear',self.clear),('Open wheel',self.open_wheel)]:
            b=QPushButton(label); b.clicked.connect(fn); row.addWidget(b)
        title=QLabel('AVAILABLE ACTIONS'); title.setObjectName('eyebrow'); v.addWidget(title)
        self.action_host=QWidget(); self.grid=QGridLayout(self.action_host); self.grid.setContentsMargins(0,0,0,0); self.grid.setSpacing(10); v.addWidget(self.action_host)
        self.hint=QLabel('Add files to see compatible actions. Select a subset to work with mixed formats.'); self.hint.setObjectName('muted'); self.hint.setWordWrap(True); v.addWidget(self.hint)
        v.addStretch()
        self.status=QLabel('Ready  •  Outputs are saved beside originals with new names.'); self.status.setWordWrap(True); v.addWidget(self.status)
        self.progress=QProgressBar(); self.progress.setTextVisible(False); self.progress.hide(); v.addWidget(self.progress)
        resultrow=QHBoxLayout(); v.addLayout(resultrow)
        self.open_result=QPushButton('Open result'); self.open_result.clicked.connect(self.open_output); self.open_result.setEnabled(False); resultrow.addWidget(self.open_result)
        self.folder_result=QPushButton('Show output folder'); self.folder_result.clicked.connect(self.open_folder); self.folder_result.setEnabled(False); resultrow.addWidget(self.folder_result)
        self.cancel=QPushButton('Cancel'); self.cancel.clicked.connect(self.cancel_job); self.cancel.hide(); resultrow.addWidget(self.cancel); resultrow.addStretch()
        foot=QLabel('Explorer: Ctrl + Alt + Space   •   Shift-drag: experimental   •   v0.1.1'); foot.setObjectName('muted'); resultrow.addWidget(foot)
        self.tray=None
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray=QSystemTrayIcon(icon(),self); self.tray.setToolTip('Prism — offline file tools'); menu=QMenu()
            menu.addAction('Open Prism',self.restore); menu.addAction('Add files',self.pick); menu.addAction('Quit',self.quit_app)
            self.tray_menu=menu; self.tray.setContextMenu(menu); self.tray.activated.connect(lambda reason:self.restore() if reason==QSystemTrayIcon.DoubleClick else None); self.tray.show()
        self.rebuild_actions()
    def restore(self): self.showNormal(); self.raise_(); self.activateWindow()
    def pick(self):
        files,_=QFileDialog.getOpenFileNames(self,'Choose files','','Supported files (*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff *.pdf *.txt *.docx)')
        self.add_files(files)
    def add_files(self,paths):
        rejected=[]
        for name in paths:
            p=Path(name)
            if not p.is_file() or p.suffix.lower() not in SUPPORTED: rejected.append(p.name); continue
            key=str(p.resolve())
            if key in self.paths: continue
            self.paths.append(key); item=QListWidgetItem(f'{p.name}    ·    {p.stat().st_size/1024:,.0f} KB'); item.setData(Qt.UserRole,key); item.setToolTip(key); self.files.addItem(item)
        self.rebuild_actions()
        if rejected: QMessageBox.information(self,'Unsupported items','Folders or unsupported files were skipped:\n'+'\n'.join(rejected[:10]))
    def selected(self):
        selected=self.files.selectedItems()
        return [i.data(Qt.UserRole) for i in selected] if selected else list(self.paths)
    def remove(self):
        for item in self.files.selectedItems(): self.paths.remove(item.data(Qt.UserRole)); self.files.takeItem(self.files.row(item))
        self.rebuild_actions()
    def clear(self): self.paths=[]; self.files.clear(); self.rebuild_actions()
    def actions(self,paths):
        ext={Path(p).suffix.lower() for p in paths}
        if not ext: return []
        if ext<=IMAGES:
            a=[('png','PNG'),('jpg','JPG'),('webp','WebP'),('images_pdf','Create PDF'),('resize','Resize'),('rotate_image','Rotate 90°'),('compress_image','Compress'),('ocr','Extract text (OCR)')]
            if len(paths)==1: a.insert(4,('crop','Crop'))
            return a
        if ext=={'.pdf'}:
            a=[('pdf_png','Page images'),('text','Extract text'),('split','Split pages'),('rotate_pdf','Rotate pages'),('ocr','Scan text (OCR)')]
            if len(paths)>1: a.insert(0,('merge','Merge PDFs'))
            else: a.insert(0,('extract','Organize pages'))
            return a
        if ext=={'.txt'}: return [('txt_pdf','Create PDF')]
        if ext=={'.docx'}: return [('docx_pdf','Create PDF')]
        return []
    def rebuild_actions(self):
        while self.grid.count():
            item=self.grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        paths=self.selected(); self.selection.setText(f'{len(paths)} selected / {len(self.paths)} files' if paths else 'Images · PDF · TXT · DOCX')
        for i,(key,label) in enumerate(self.actions(paths)):
            b=QPushButton(label+'  ↗'); b.setMinimumHeight(47); b.setEnabled(self.job is None); b.clicked.connect(lambda checked=False,k=key:self.start(k)); self.grid.addWidget(b,i//4,i%4)
        self.hint.setText('Select matching file types to enable actions.' if paths and not self.actions(paths) else 'New files are saved beside originals. Metadata is not retained in image exports; colour is normalized to sRGB.')
    def open_wheel(self):
        self.show_wheel(self.selected(),False)
    def show_wheel(self,paths,drag):
        if self.job: return
        actions=self.actions(paths)
        if not actions: self.restore(); return
        self.wheel_paths=list(paths)
        # First wheel is conversion + tools selector, never silently hide actions.
        if {Path(p).suffix.lower() for p in paths}<=IMAGES:
            actions=[('png','PNG'),('jpg','JPG'),('webp','WebP'),('images_pdf','PDF'),('_tools','Tools')]
        self.wheel.present(actions,Path(paths[0]).name if len(paths)==1 else f'{len(paths)} files',drag)
    def set_wheel_paths(self,paths): self.wheel_paths=paths
    def wheel_action(self,key):
        if key=='_tools':
            actions=[a for a in self.actions(self.wheel_paths) if a[0] not in ('png','jpg','webp','images_pdf')]
            QTimer.singleShot(0,lambda:self.wheel.present(actions,'Image tools',False)); return
        self.start(key,self.wheel_paths)
    def explorer_wheel(self,paths,drag):
        paths=[p for p in paths if Path(p).is_file() and Path(p).suffix.lower() in SUPPORTED]
        if paths: self.show_wheel(paths,drag)
        elif not drag: self.restore(); self.status.setText('Select supported files in a File Explorer window, or add files here.')
    def start(self,key,paths=None):
        if self.job: return
        paths=list(paths or self.selected()); options={}
        if not paths: return
        try:
            if key=='jpg' or (key in ('crop','resize','rotate_image','compress_image') and any(Path(p).suffix.lower() in ('.jpg','.jpeg') for p in paths)):
                if QMessageBox.question(self,'JPEG output','JPEG is lossy. Transparent areas become white. Originals stay unchanged. Continue?')!=QMessageBox.Yes: return
            if key=='crop':
                dialog=CropDialog(paths[0],self)
                if dialog.exec()!=QDialog.Accepted: return
                options['box']=dialog.canvas.box()
                if not options['box']: raise ValueError('Drag a crop rectangle before saving.')
            if key=='resize':
                width,ok=QInputDialog.getInt(self,'Resize','Maximum width (pixels). Aspect ratio is preserved; smaller images are not enlarged.',1600,1,30000)
                if not ok:return
                options['width']=width
            if key=='compress_image':
                quality,ok=QInputDialog.getInt(self,'Compression','JPEG/WebP quality (lower = smaller, lossy). PNG uses lossless optimization and may not shrink.',85,20,100)
                if not ok:return
                options.update(quality=quality,lossy=True)
            if key=='extract':
                dialog=PagesDialog(paths[0],self)
                if dialog.exec()!=QDialog.Accepted:return
                options['pages']=dialog.sequence()
                if not options['pages']:raise ValueError('Keep at least one page.')
            if key in ('pdf_png','split','rotate_pdf'):
                pages,ok=QInputDialog.getText(self,'Choose pages','Pages: 1,3,5-8. Leave empty for all pages. Applied to each selected PDF.')
                if not ok:return
                options['pages']=pages
            if key=='pdf_png':
                dpi,ok=QInputDialog.getInt(self,'Image resolution','DPI (150 is faster; 300 is suitable for printing)',150,72,300)
                if not ok:return
                options['dpi']=dpi
            if key=='docx_pdf':
                if QMessageBox.question(self,'Document rendering','Uses locally installed LibreOffice. Fonts and complex layouts may differ from Word. Review the resulting PDF. Continue?')!=QMessageBox.Yes:return
            if key=='ocr':
                if QMessageBox.question(self,'OCR','Printed-text OCR is optional and can make mistakes. Review the extracted text before using it. Continue?')!=QMessageBox.Yes:return
            self.job=Job(key,paths,options); self.active_action=key
            self.job.signals.progress.connect(self.update_progress)
            self.job.signals.success.connect(self.succeeded); self.job.signals.failure.connect(self.failed); self.job.signals.finished.connect(self.finished)
            self.progress.setRange(0,0); self.progress.show(); self.cancel.show(); self.cancel.setEnabled(True)
            self.status.setText('Working… '+dict(self.actions(paths)).get(key,key)); self.open_result.setEnabled(False); self.folder_result.setEnabled(False); self.rebuild_actions(); self.pool.start(self.job)
        except Exception as e: QMessageBox.warning(self,'Cannot start',str(e))
    def update_progress(self,n,total):
        self.progress.setRange(0,100); self.progress.setValue(round(n*100/max(total,1)))
    def cancel_job(self):
        if self.job: self.job.cancel.set(); self.cancel.setEnabled(False); self.status.setText('Cancelling after the current engine step…')
    def succeeded(self,outputs):
        self.outputs=outputs; self.status.setText(f'Completed • {len(outputs)} output file(s) • {Path(outputs[0]).name}')
        self.open_result.setEnabled(True); self.folder_result.setEnabled(True)
        if self.active_action in ('ocr','text') and len(outputs)==1: QTimer.singleShot(0,lambda:self.text_preview(outputs[0]))
    def failed(self,message): self.status.setText(message)
    def finished(self): self.job=None; self.cancel.hide(); self.progress.hide(); self.rebuild_actions()
    def open_output(self):
        if self.outputs: QDesktopServices.openUrl(QUrl.fromLocalFile(self.outputs[0]))
    def open_folder(self):
        if self.outputs: QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(self.outputs[0]).parent)))
    def text_preview(self,path):
        d=QDialog(self); d.setWindowTitle('Review extracted text'); d.resize(740,560); v=QVBoxLayout(d)
        v.addWidget(QLabel('Review and correct text. The saved extraction is unchanged unless you save a revised copy.'))
        edit=QPlainTextEdit(); edit.setPlainText(Path(path).read_text(encoding='utf-8')); v.addWidget(edit)
        h=QHBoxLayout(); v.addLayout(h)
        b=QPushButton('Copy text'); b.clicked.connect(lambda:QApplication.clipboard().setText(edit.toPlainText())); h.addWidget(b)
        def save_revision():
            from .engine import commit
            p=commit(Path(path),'.txt',' - revised',lambda p:p.write_text(edit.toPlainText(),encoding='utf-8'),lambda p:p.read_text(encoding='utf-8'))
            self.outputs=[str(p)]; d.accept()
        b=QPushButton('Save revised copy'); b.clicked.connect(save_revision); h.addWidget(b)
        b=QPushButton('Close'); b.clicked.connect(d.accept); h.addWidget(b); d.exec()
    def preferences(self):
        d=QDialog(self); d.setWindowTitle('Prism settings'); v=QVBoxLayout(d)
        c=QCheckBox('Enable Explorer shortcut and experimental Shift-drag'); c.setChecked(self.bridge.enabled); v.addWidget(c)
        t=QCheckBox('Close window to system tray'); t.setChecked(self.settings.value('tray',True,type=bool)); v.addWidget(t)
        theme=QComboBox(); theme.addItems(['System','Dark','Light']); theme.setCurrentText(self.settings.value('theme','Dark')); v.addWidget(QLabel('Appearance')); v.addWidget(theme)
        text=QLabel('Fluent-inspired surfaces with a solid fallback.\nOptional: run Install-OCR.bat for OCR; install LibreOffice for DOCX.\nNo files are uploaded. No sharing or cloud service.\nExplorer integration must be verified on your Windows installation.'); text.setWordWrap(True); v.addWidget(text)
        b=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel); v.addWidget(b); b.accepted.connect(d.accept); b.rejected.connect(d.reject)
        if d.exec()==QDialog.Accepted:
            self.bridge.enabled=c.isChecked(); self.settings.setValue('explorer',c.isChecked()); self.settings.setValue('tray',t.isChecked()); self.settings.setValue('theme',theme.currentText()); self.wheel.light=not set_theme(theme.currentText())
    def quit_app(self):
        if self.job:
            self.cancel_job(); QMessageBox.information(self,'Job stopping','Wait for the current operation to stop, then quit again.'); return
        self.quitting=True; self.close()
    def closeEvent(self,e):
        if self.job: self.hide(); e.ignore(); return
        if self.tray and not getattr(self,'quitting',False) and self.settings.value('tray',True,type=bool): self.hide(); e.ignore(); return
        self.wheel.close(); e.accept(); QApplication.quit()

def main():
    app=QApplication(sys.argv); app.setApplicationName('Prism'); app.setStyle('Fusion'); app.setStyleSheet(DARK); app.setWindowIcon(icon())
    w=Window(); w.show()
    if len(sys.argv)>1:w.add_files(sys.argv[1:])
    sys.exit(app.exec())
