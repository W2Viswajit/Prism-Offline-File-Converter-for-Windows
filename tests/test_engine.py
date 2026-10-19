import sys, threading, hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
from PIL import Image
from pypdf import PdfReader,PdfWriter
from reportlab.pdfgen import canvas
from prism.engine import run,pages_from_text,Cancelled,commit

@pytest.fixture
def fixtures(tmp_path):
    img=tmp_path/'透明 photo.png'; Image.new('RGBA',(320,180),(30,120,200,120)).save(img)
    pdf=tmp_path/'notes.pdf'; c=canvas.Canvas(str(pdf))
    for i in range(3): c.drawString(80,750,f'Prism test page {i+1}'); c.showPage()
    c.save()
    txt=tmp_path/'text.txt'; txt.write_text('Viswajit — test\nA clear document.\n'+'Long line '*300,encoding='utf8')
    return img,pdf,txt

@pytest.mark.parametrize('action',['png','jpg','webp','resize','rotate_image','compress_image','crop'])
def test_image_routes(fixtures,action):
    img,_,_=fixtures; before=hashlib.sha256(img.read_bytes()).digest()
    opts={'width':160,'box':(20,30,120,130)}
    out=run(action,[img],opts)[0]
    with Image.open(out) as im:
        expected=(160,90) if action=='resize' else (180,320) if action=='rotate_image' else (100,100) if action=='crop' else (320,180)
        assert im.size==expected
        if action in ('png','webp'): assert im.convert('RGBA').getpixel((0,0))==(30,120,200,120)
        if action=='jpg': assert im.mode=='RGB'
    assert hashlib.sha256(img.read_bytes()).digest()==before

def test_no_overwrite(fixtures):
    img,_,_=fixtures; a=run('png',[img])[0]; b=run('png',[img])[0]
    assert a!=b and a.exists() and b.exists()

def test_pdf_tools(fixtures):
    _,pdf,_=fixtures
    merge=run('merge',[pdf,pdf])[0]; assert len(PdfReader(merge).pages)==6
    extracted=run('extract',[pdf],{'pages':'3,1'})[0]; r=PdfReader(extracted)
    assert len(r.pages)==2 and 'page 3' in r.pages[0].extract_text() and 'page 1' in r.pages[1].extract_text()
    rotated=run('rotate_pdf',[pdf])[0]; assert PdfReader(rotated).pages[0].rotation==90
    split=run('split',[pdf])[0]; assert len(PdfReader(split).pages)==1
    images=run('pdf_png',[pdf],{'pages':'2','dpi':72}); assert len(images)==1
    Image.open(images[0]).verify()

def test_text_and_images_pdf(fixtures):
    img,pdf,txt=fixtures
    assert len(PdfReader(run('images_pdf',[img,img])[0]).pages)==2
    assert 'page 2' in run('text',[pdf])[0].read_text()
    result=PdfReader(run('txt_pdf',[txt])[0]); assert 'Viswajit' in result.pages[0].extract_text()

@pytest.mark.parametrize('value',['0','4','1-5','abc','1,','-1'])
def test_bad_page_ranges(value):
    with pytest.raises(ValueError): pages_from_text(value,3)

def test_reverse_pages(): assert pages_from_text('3-1',3)==[2,1,0]

def test_cancellation(fixtures):
    event=threading.Event(); event.set()
    with pytest.raises(Cancelled):run('png',[fixtures[0]],cancel=event)
    assert not list(fixtures[0].parent.glob('* - png*'))

def test_invalid_output_cleaned(tmp_path):
    source=tmp_path/'source.txt'; source.write_text('hello')
    def invalid(p): raise ValueError('bad output')
    with pytest.raises(ValueError):commit(source,'.txt',' - out',lambda p:p.write_text('bad'),invalid)
    assert list(tmp_path.iterdir())==[source]

def test_encrypted_rejected(fixtures):
    _,pdf,_=fixtures; w=PdfWriter(); w.append(str(pdf)); w.encrypt('secret'); path=pdf.parent/'encrypted.pdf'; w.write(str(path))
    with pytest.raises(ValueError,match='encrypted'):run('text',[path])

def test_empty_text_layer(fixtures):
    img,_,_=fixtures; pdf=run('images_pdf',[img])[0]
    with pytest.raises(ValueError,match='OCR'):run('text',[pdf])

def test_crop_bounds(fixtures):
    with pytest.raises(ValueError):run('crop',[fixtures[0]],{'box':(-1,0,100,100)})

def test_multi_frame_rejected(tmp_path):
    p=tmp_path/'multi.tiff'; im=Image.new('RGB',(10,10)); im.save(p,save_all=True,append_images=[im])
    with pytest.raises(ValueError,match='Multi-frame'):run('png',[p])
