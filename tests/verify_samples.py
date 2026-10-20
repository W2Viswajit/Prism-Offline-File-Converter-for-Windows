"""Generate verifiable examples without touching original samples.
Run: .venv\\Scripts\\python.exe tests\\verify_samples.py
"""
import hashlib,html,json,sys,time
from datetime import datetime
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from prism.engine import run,reader,find_office
from PIL import Image
import pypdfium2 as pdfium
root=Path(__file__).resolve().parents[1]; samples=root/'samples'
out=samples/('phase1-'+datetime.now().strftime('%Y%m%d-%H%M%S')); out.mkdir()
originals={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in samples.iterdir() if p.is_file()}
img=samples/'sample-image.png'; scan=samples/'sample-scan.png'; pdf=samples/'sample-document.pdf'; txt=samples/'sample-text.txt'
results=[]
def example(key,paths,options=None,label=None):
    folder=out/(label or key); folder.mkdir()
    start=time.perf_counter(); outputs=run(key,paths,dict(options or {},folder=folder))
    row={'tool':label or key,'seconds':round(time.perf_counter()-start,2),'outputs':[str(p.relative_to(out)) for p in outputs],'previews':[],'checks':[]}
    for index,p in enumerate(outputs):
        if p.suffix=='.pdf':
            r=reader(p); row['checks'].append(f'{p.name}: {len(r.pages)} pages')
            doc=pdfium.PdfDocument(str(p))
            try:
                for number in range(len(doc)):
                    page=doc[number]
                    try:
                        bitmap=page.render(scale=min(1.0,640/page.get_width()))
                        try:
                            preview=folder/f'preview-{index+1}-{number+1}.png'; bitmap.to_pil().save(preview); row['previews'].append(str(preview.relative_to(out)))
                        finally: bitmap.close()
                    finally: page.close()
            finally: doc.close()
        elif p.suffix=='.txt':
            text=p.read_text(encoding='utf-8'); assert text.strip(); row['text']=text
        else:
            with Image.open(p) as im:
                im.load(); row['checks'].append(f'{p.name}: {im.width} x {im.height}, {im.mode}')
                preview=folder/f'preview-{index+1}.png'; im.thumbnail((640,480)); im.save(preview); row['previews'].append(str(preview.relative_to(out)))
    results.append(row); print(row['tool'],row['seconds'],'seconds',flush=True)
    return outputs,row

for key,options in [('png',{}),('jpg',{}),('webp',{}),('resize',{'width':320}),('rotate_image',{}),('compress_image',{}),('crop',{'box':(20,20,220,160)})]:
    example(key,[img],options)
image_pdf,_=example('images_pdf',[img,scan]); assert len(reader(image_pdf[0]).pages)==2
merged,_=example('merge',[pdf,pdf]); assert len(reader(merged[0]).pages)==len(reader(pdf).pages)*2
count=len(reader(pdf).pages)
organized,_=example('extract',[pdf],{'pages':f'{count},1'}); assert len(reader(organized[0]).pages)==2
assert reader(organized[0]).pages[0].extract_text()==reader(pdf).pages[count-1].extract_text()
rotated,_=example('rotate_pdf',[pdf],{'pages':'1'}); r=reader(rotated[0]); assert len(r.pages)==count
assert r.pages[0].rotation==(reader(pdf).pages[0].rotation+90)%360
assert all(r.pages[i].rotation==reader(pdf).pages[i].rotation for i in range(1,count))
split,_=example('split',[pdf]); assert len(split)==count and all(len(reader(p).pages)==1 for p in split)
rendered,_=example('pdf_png',[pdf],{'dpi':150}); assert len(rendered)==count
text,_=example('text',[pdf]); assert text[0].read_text(encoding='utf-8').strip()
example('txt_pdf',[txt])
ocr_image,_=example('ocr',[scan],label='ocr-image'); assert 'Prism' in ocr_image[0].read_text(encoding='utf-8')
scan_pdf,_=example('images_pdf',[scan],label='scanned-pdf-input')
ocr_pdf,_=example('ocr',[scan_pdf[0]],label='ocr-pdf'); assert 'Prism' in ocr_pdf[0].read_text(encoding='utf-8')
assert all(hashlib.sha256(p.read_bytes()).hexdigest()==digest for p,digest in originals.items())
report={'results':results,'originals_unchanged':True,'libreoffice':find_office(),'platform':sys.platform,'python':sys.version}
(out/'results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
esc=html.escape
cards=[]
for row in results:
    links=' '.join(f'<a href="{esc(p.replace(chr(92),"/"))}">Open output {i+1}</a>' for i,p in enumerate(row['outputs']))
    previews=''.join(f'<img loading="lazy" src="{esc(p.replace(chr(92),"/"))}">' for p in row['previews'])
    text=f'<pre>{esc(row.get("text",""))}</pre>' if 'text' in row else ''
    cards.append(f'<section id="{row["tool"]}"><h2>{esc(row["tool"])} <small>Verified · {row["seconds"]} s</small></h2><p>{esc(" | ".join(row["checks"]))}</p><p>{links}</p><div class="previews">{previews}</div>{text}</section>')
nav=''.join(f'<a href="#{r["tool"]}">{r["tool"]}</a>' for r in results)
(out/'index.html').write_text('''<!doctype html><meta charset="utf-8"><title>Prism — verified tool samples</title><style>body{font:16px Segoe UI,sans-serif;background:#111923;color:#ecf2fa;margin:32px auto;max-width:1120px;padding:0 24px}h1{font-size:38px}section{background:#1c2838;border:1px solid #42536a;padding:24px;border-radius:16px;margin:24px 0}small{font-size:14px;color:#a6e0bb;float:right}a{color:#b4d5ff;margin:8px;display:inline-block}nav{position:sticky;top:0;background:#111923;z-index:1;max-height:120px;overflow:auto;border-bottom:1px solid #42536a}.previews{display:flex;gap:16px;overflow:auto}img{max-height:450px;max-width:90%;object-fit:contain;background:repeating-conic-gradient(#ddd 0% 25%,#fff 0% 50%) 50%/20px 20px}pre{white-space:pre-wrap;background:#101722;padding:20px}p{color:#c0cedf}</style><h1>Prism / Verified tool samples</h1><p>Actual outputs from the conversion engine on Windows. Originals were checked with SHA-256 and remain unchanged. PDF previews include every output page. This report is a saved demonstration, not a substitute for Explorer interaction testing.</p><nav>'''+nav+'</nav>'+''.join(cards),encoding='utf-8')
print('REPORT',out,flush=True)

