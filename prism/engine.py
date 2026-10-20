"""Offline conversion engine. Never modifies inputs; commits validated files exclusively."""
from pathlib import Path
from threading import Event
import os, tempfile, shutil, subprocess, time, io
from PIL import Image, ImageOps, ImageCms
from pypdf import PdfReader, PdfWriter

IMAGES = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tif', '.tiff'}
SUPPORTED = IMAGES | {'.pdf', '.txt', '.docx'}
class Cancelled(Exception): pass

def check(cancel):
    if cancel and cancel.is_set(): raise Cancelled('Cancelled. Completed outputs were kept.')

def pages_from_text(value, count):
    if not value.strip(): return list(range(count))
    result=[]
    for part in value.split(','):
        p=part.strip().split('-')
        if len(p)==1: result.append(int(p[0])-1)
        elif len(p)==2:
            a,b=map(int,p)
            result.extend(range(a-1,b,1) if a<=b else range(a-1,b-2,-1))
        else: raise ValueError('Use pages such as 1,3,5-8 or 4,2,1.')
    if not result or any(i<0 or i>=count for i in result): raise ValueError(f'Page numbers must be between 1 and {count}.')
    return result

def reader(path):
    r=PdfReader(path)
    if r.is_encrypted: raise ValueError('This PDF is encrypted. Open an unprotected copy first.')
    return r

def commit(source, suffix, tag, write, validate, folder=None, cancel=None):
    base=Path(folder) if folder else Path(source).parent
    base.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.prism-',suffix=suffix,dir=base); os.close(fd)
    tmp=Path(tmp)
    try:
        check(cancel); write(tmp); check(cancel); validate(tmp)
        for n in range(1,100000):
            name=f'{Path(source).stem}{tag}' + (f' ({n})' if n>1 else '') + suffix
            dest=base/name
            try:
                # Exclusive creation prevents even concurrent jobs from overwriting a file.
                with dest.open('xb') as out:
                    try:
                        with tmp.open('rb') as inp: shutil.copyfileobj(inp,out)
                    except BaseException:
                        out.close(); dest.unlink(missing_ok=True); raise
                return dest
            except FileExistsError: continue
        raise RuntimeError('Cannot choose a free output filename.')
    finally: tmp.unlink(missing_ok=True)

def validate_pdf(path):
    if not len(reader(path).pages): raise ValueError('Output has no PDF pages.')

def validate_image(path):
    with Image.open(path) as im: im.verify()

def load_image(path):
    with Image.open(path) as original:
        if getattr(original,'n_frames',1)>1: raise ValueError('Multi-frame images are not supported in V1. Export individual frames first.')
        if original.width*original.height>60_000_000: raise ValueError('Image exceeds V1’s 60 megapixel limit.')
        im=ImageOps.exif_transpose(original).copy()
        profile=original.info.get('icc_profile')
        if profile:
            try:
                alpha=im.getchannel('A') if im.mode=='RGBA' else None
                im=ImageCms.profileToProfile(im,io.BytesIO(profile),ImageCms.createProfile('sRGB'),outputMode='RGB')
                if alpha: im.putalpha(alpha)
            except Exception as e: raise ValueError('Cannot safely convert this image colour profile.') from e
        if im.mode not in ('RGB','RGBA'): im=im.convert('RGBA' if 'transparency' in im.info else 'RGB')
        return im

def rgb(im):
    if im.mode=='RGBA':
        bg=Image.new('RGB',im.size,'white'); bg.paste(im,mask=im.getchannel('A')); return bg
    return im.convert('RGB')

def run(action, paths, options=None, cancel=None, progress=None):
    options=options or {}; paths=[Path(p) for p in paths]
    cancel=cancel or Event(); progress=progress or (lambda a,b:None)
    if not paths: raise ValueError('Choose at least one file.')
    for p in paths:
        if not p.is_file(): raise ValueError(f'File not found: {p}')
    output=[]; folder=options.get('folder')
    def save(src,ext,tag,write,validate):
        p=commit(src,ext,tag,write,validate,folder,cancel); output.append(p); return p
    def pdfsave(src,tag,w):
        return save(src,'.pdf',tag,lambda p:w.write(str(p)),validate_pdf)
    if action=='images_pdf':
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader
        def build(p):
            c=canvas.Canvas(str(p))
            for i,src in enumerate(paths):
                check(cancel); im=rgb(load_image(src)); width,height=im.size
                c.setPageSize((width*72/150,height*72/150))
                c.drawImage(ImageReader(im),0,0,width=width*72/150,height=height*72/150)
                c.showPage(); progress(i+1,len(paths))
            c.save()
        save(paths[0],'.pdf',' - images',build,validate_pdf); return output
    if action=='merge':
        w=PdfWriter()
        for i,p in enumerate(paths):
            check(cancel); w.append(reader(p)); progress(i+1,len(paths))
        pdfsave(paths[0],' - merged',w); return output
    for index,src in enumerate(paths):
        check(cancel); ext=src.suffix.lower()
        if action in ('png','jpg','webp','resize','crop','rotate_image','compress_image'):
            im=load_image(src)
            target=action if action in ('png','jpg','webp') else ('jpg' if ext in ('.jpg','.jpeg') else 'webp' if ext=='.webp' else 'png')
            if action=='resize':
                max_width=int(options.get('width',1600))
                if max_width<1: raise ValueError('Width must be positive.')
                if max_width<im.width or options.get('upscale',False): im=im.resize((max_width,max(1,round(im.height*max_width/im.width))),Image.Resampling.LANCZOS)
            if action=='crop':
                box=options.get('box')
                if not box or len(box)!=4: raise ValueError('Select a crop area.')
                l,t,r,b=map(int,box)
                if not (0<=l<r<=im.width and 0<=t<b<=im.height): raise ValueError('Crop is outside image bounds.')
                im=im.crop((l,t,r,b))
            if action=='rotate_image': im=im.transpose(Image.Transpose.ROTATE_270)
            if target=='jpg': im=rgb(im)
            kw={'icc_profile':ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()}
            if target=='jpg': kw.update(quality=int(options.get('quality',95)),subsampling=0,optimize=True)
            if target=='webp': kw.update(lossless=not options.get('lossy',False),quality=int(options.get('quality',90)),method=4)
            if target=='png': kw.update(optimize=True)
            save(src,'.'+target,' - '+action,lambda p:im.save(p,format={'jpg':'JPEG','png':'PNG','webp':'WEBP'}[target],**kw),validate_image)
        elif action in ('extract','rotate_pdf','split'):
            r=reader(src); ids=pages_from_text(options.get('pages',''),len(r.pages))
            if action=='split':
                for page in ids:
                    check(cancel); w=PdfWriter(); w.add_page(r.pages[page]); pdfsave(src,f' - page {page+1}',w)
            else:
                w=PdfWriter()
                for page in ids:
                    obj=w.add_page(r.pages[page])
                    if action=='rotate_pdf': obj.rotate(90)
                pdfsave(src,' - '+action,w)
        elif action=='pdf_png':
            import pypdfium2 as pdfium
            reader(src) # Reject encrypted inputs consistently.
            doc=pdfium.PdfDocument(str(src))
            try:
                ids=pages_from_text(options.get('pages',''),len(doc))
                for page_no in ids:
                    check(cancel); page=doc[page_no]
                    if page.get_width()*page.get_height()*(options.get('dpi',150)/72)**2>60_000_000:
                        page.close(); raise ValueError('Rendered page exceeds 60 megapixels. Use a lower DPI.')
                    bitmap=page.render(scale=options.get('dpi',150)/72); im=bitmap.to_pil()
                    save(src,'.png',f' - page {page_no+1}',lambda p:im.save(p),validate_image)
                    bitmap.close(); page.close()
            finally: doc.close()
        elif action in ('text','ocr'):
            if action=='text':
                text='\n\n'.join(p.extract_text() or '' for p in reader(src).pages)
                if not text.strip(): raise ValueError('No embedded text found. Use OCR for scanned pages.')
            else: text=ocr(src,cancel)
            save(src,'.txt',' - text',lambda p:p.write_text(text,encoding='utf-8'),lambda p:p.read_text(encoding='utf-8'))
        elif action=='txt_pdf':
            text=src.read_text(encoding='utf-8-sig')
            def textpdf(p):
                from reportlab.pdfgen import canvas
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont
                fontpaths=[Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts/arial.ttf',Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')]
                fontpath=next((f for f in fontpaths if f.exists()),None)
                if not fontpath: raise ValueError('A Unicode TrueType font is required (Windows Arial).')
                pdfmetrics.registerFont(TTFont('PrismText',str(fontpath)))
                c=canvas.Canvas(str(p),pagesize=(595,842)); c.setFont('PrismText',11); y=792
                for line in text.expandtabs(4).splitlines() or ['']:
                    check(cancel)
                    chunks=[]; buf=''
                    for ch in line:
                        if pdfmetrics.stringWidth(buf+ch,'PrismText',11)>495:
                            chunks.append(buf); buf=''
                        buf+=ch
                    chunks.append(buf)
                    for chunk in chunks:
                        if y<50: c.showPage(); c.setFont('PrismText',11); y=792
                        c.drawString(50,y,chunk); y-=16
                c.save()
            save(src,'.pdf',' - text',textpdf,validate_pdf)
        elif action=='docx_pdf':
            exe=find_office()
            if not exe: raise ValueError('Install LibreOffice to enable DOCX to PDF, then restart Prism. Other tools work without it.')
            with tempfile.TemporaryDirectory(prefix='prism-office-') as tmp:
                root=Path(tmp); profile=(root/'profile').as_uri()
                cmd=[exe,f'-env:UserInstallation={profile}','--headless','--convert-to','pdf','--outdir',tmp,str(src.resolve())]
                proc=subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=0x08000000 if os.name=='nt' else 0)
                start=time.monotonic()
                try:
                    while proc.poll() is None:
                        check(cancel)
                        if time.monotonic()-start>120: raise TimeoutError('Document rendering exceeded two minutes.')
                        time.sleep(.1)
                    generated=root/(src.stem+'.pdf')
                    if proc.returncode or not generated.exists(): raise ValueError('LibreOffice could not render this document.')
                    save(src,'.pdf',' - document',lambda p:shutil.copyfile(generated,p),validate_pdf)
                finally:
                    if proc.poll() is None: proc.kill(); proc.wait()
        else: raise ValueError(f'Unsupported operation: {action}')
        progress(index+1,len(paths))
    return output

def find_office():
    candidates=[shutil.which('soffice'),r'C:\Program Files\LibreOffice\program\soffice.exe',r'C:\Program Files (x86)\LibreOffice\program\soffice.exe']
    return next((str(p) for p in candidates if p and Path(p).exists()),None)

def ocr(path,cancel):
    try:
        from rapidocr import RapidOCR
        import numpy as np
    except ImportError as e: raise ValueError('OCR is optional. Run Install-OCR.bat once, then restart Prism.') from e
    fontpaths=[Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts/arial.ttf',
               Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')]
    font=next((f for f in fontpaths if f.exists()),None)
    if font is None: raise ValueError('OCR requires a local TrueType font (Windows Arial).')
    engine=RapidOCR(params={'Global.font_path':str(font),
                           'EngineConfig.onnxruntime.intra_op_num_threads':2,
                           'EngineConfig.onnxruntime.inter_op_num_threads':1})
    texts=[]
    def recognize(im):
        check(cancel); result=engine(np.asarray(rgb(im)))
        texts.append('\n'.join(result.txts or []))
    if path.suffix.lower()=='.pdf':
        import pypdfium2 as pdfium
        reader(path); doc=pdfium.PdfDocument(str(path))
        try:
            for i in range(len(doc)):
                check(cancel); page=doc[i]
                scale=min(2.0,(40_000_000/(page.get_width()*page.get_height()))**.5)
                bm=page.render(scale=scale)
                try: recognize(bm.to_pil())
                finally: bm.close(); page.close()
        finally: doc.close()
    else: recognize(load_image(path))
    text='\n\n'.join(texts)
    if not text.strip(): raise ValueError('OCR found no readable text.')
    return text
