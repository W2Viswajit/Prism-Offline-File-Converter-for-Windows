"""Live, replayable engine demonstration. All generated files stay in samples.
This harness supplies fixed demo options; it does not replace manual dialog testing.
"""
import sys,json
from pathlib import Path
from datetime import datetime
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication,QWidget,QVBoxLayout,QHBoxLayout,QLabel,QComboBox,QPushButton,QPlainTextEdit
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt,QThreadPool,QTimer
from PIL.ImageQt import ImageQt
import pypdfium2 as pdfium
from prism.ui import Job
from prism.theme import appearance,stylesheet
root=Path(__file__).resolve().parents[1]; samples=root/'samples'
img=samples/'sample-image.png'; scan=samples/'sample-scan.png'; pdf=samples/'sample-document.pdf'; txt=samples/'sample-text.txt'
cases=[(k,k,[img],o) for k,o in [('png',{}),('jpg',{}),('webp',{}),('resize',{'width':320}),('crop',{'box':(20,20,220,160)}),('rotate_image',{}),('compress_image',{})]]
cases += [('Create PDF','images_pdf',[img,scan],{}),('Merge PDFs','merge',[pdf,pdf],{}),('Organize pages','extract',[pdf],{'pages':'2,1'}),('Rotate selected page','rotate_pdf',[pdf],{'pages':'1'}),('Split pages','split',[pdf],{}),('PDF page images','pdf_png',[pdf],{'dpi':150}),('Extract PDF text','text',[pdf],{}),('Text to PDF','txt_pdf',[txt],{}),('Image OCR','ocr',[scan],{})]
scan_pdfs=sorted(samples.glob('phase1-*/scanned-pdf-input/*.pdf'))
if scan_pdfs: cases.append(('PDF OCR','ocr',[scan_pdfs[-1]],{}))
word_samples=sorted(samples.glob('word-demo-*/Prism Word sample.docx'))
if word_samples: cases.append(('Microsoft Word to PDF','docx_pdf',[word_samples[-1]],{}))
class Demo(QWidget):
    def __init__(self):
        super().__init__(); self.setWindowTitle('Prism - live tool verification'); self.resize(1000,800)
        self.output=samples/('live-demo-'+datetime.now().strftime('%Y%m%d-%H%M%S')); self.output.mkdir()
        self.pool=QThreadPool(self); self.pool.setMaxThreadCount(1); self.job=None; self.records=[]; self.auto=True
        v=QVBoxLayout(self); title=QLabel('PRISM / LIVE TOOL VERIFICATION'); title.setStyleSheet('font-size:24px;font-weight:600'); v.addWidget(title)
        v.addWidget(QLabel('Real conversion jobs using the supplied samples. Outputs and preview captures are saved in samples.'))
        h=QHBoxLayout(); v.addLayout(h); self.choose=QComboBox(); self.choose.addItems([x[0] for x in cases]); h.addWidget(self.choose)
        self.replay=QPushButton('Run selected tool'); self.replay.clicked.connect(self.manual); h.addWidget(self.replay)
        pause=QPushButton('Stop automatic playback'); pause.clicked.connect(self.pause); h.addWidget(pause)
        self.status=QLabel(); self.status.setWordWrap(True); v.addWidget(self.status)
        self.preview=QLabel(); self.preview.setAlignment(Qt.AlignCenter); v.addWidget(self.preview,1)
        self.text=QPlainTextEdit(); self.text.setReadOnly(True); self.text.hide(); v.addWidget(self.text,1)
        self.files=QLabel(); self.files.setWordWrap(True); v.addWidget(self.files)
        self.next_timer=QTimer(self); self.next_timer.setSingleShot(True); self.next_timer.timeout.connect(self.advance)
        QTimer.singleShot(700,self.execute)
    def pause(self): self.auto=False; self.next_timer.stop()
    def manual(self): self.pause(); self.execute()
    def execute(self):
        if self.job: return
        index=self.choose.currentIndex()
        label,key,paths,options=cases[index]
        folder=self.output/f'{index+1:02d}-{key}'; folder.mkdir(exist_ok=True)
        self.status.setText(f'{index+1}/{len(cases)} · Running {label}…'); self.replay.setEnabled(False); self.choose.setEnabled(False)
        self.preview.clear(); self.text.hide(); self.preview.show()
        self.job=Job(key,[str(p) for p in paths],dict(options,folder=folder)); self.key=key
        self.job.signals.success.connect(self.done); self.job.signals.failure.connect(self.failed); self.job.signals.finished.connect(self.finished)
        self.pool.start(self.job)
    def done(self,outputs):
        self.records.append({'tool':self.choose.currentText(),'action':self.key,'outputs':outputs})
        p=Path(outputs[0]); self.files.setText('\n'.join(outputs))
        if p.suffix=='.txt': self.preview.hide(); self.text.show(); self.text.setPlainText(p.read_text(encoding='utf-8'))
        elif p.suffix=='.pdf':
            doc=pdfium.PdfDocument(str(p)); page=doc[0]; bitmap=page.render(scale=min(1.2,650/page.get_width()))
            try: pix=QPixmap.fromImage(ImageQt(bitmap.to_pil())).copy()
            finally: bitmap.close(); page.close(); doc.close()
            self.preview.setPixmap(pix.scaled(850,550,Qt.KeepAspectRatio,Qt.SmoothTransformation))
        else: self.preview.setPixmap(QPixmap(str(p)).scaled(850,550,Qt.KeepAspectRatio,Qt.SmoothTransformation))
        self.status.setText(f'{self.choose.currentIndex()+1}/{len(cases)} · Completed {self.choose.currentText()} · {len(outputs)} output(s) · preview: first output/page')
        (self.output/'results.json').write_text(json.dumps(self.records,indent=2),encoding='utf-8')
        QTimer.singleShot(200,self.capture)
    def capture(self): self.grab().save(str(self.output/f'{self.choose.currentIndex()+1:02d}-live-preview.png'))
    def failed(self,message): self.pause(); self.status.setText(message)
    def finished(self):
        self.job=None; self.replay.setEnabled(True); self.choose.setEnabled(True)
        if self.auto: self.next_timer.start(3500)
    def advance(self):
        index=self.choose.currentIndex()+1
        if index<self.choose.count(): self.choose.setCurrentIndex(index); self.execute()
        else: self.auto=False; self.status.setText(f'All {len(cases)} demonstrations completed. Choose any tool to replay it. Outputs and preview captures are saved in '+str(self.output))
    def closeEvent(self,event):
        self.pause()
        if self.job: self.job.cancel.set(); event.ignore()
        else: event.accept()
if __name__=='__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    app=QApplication([]); app.setStyle('Fusion'); app.setStyleSheet(stylesheet(appearance()))
    w=Demo(); w.show(); app.exec()
