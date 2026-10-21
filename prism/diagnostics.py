"""Opt-in installed-runtime check. Writes only to a new output directory."""
import hashlib,json,traceback
from pathlib import Path
from .engine import run,reader,has_word

def verify(samples,output):
    samples=Path(samples).resolve();output=Path(output).resolve()
    output.mkdir(parents=True,exist_ok=False)
    inputs=[samples/n for n in ('sample-image.png','sample-scan.png','sample-document.pdf','sample-text.txt')]
    img,scan,pdf,txt=inputs
    word=sorted(samples.glob('word-demo-*/Prism Word sample.docx'))
    if word:inputs.append(word[-1])
    hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    cases=[(k,[img],o) for k,o in [('png',{}),('jpg',{}),('webp',{}),('resize',{'width':320}),('crop',{'box':(20,20,220,160)}),('rotate_image',{}),('compress_image',{})]]
    cases += [('images_pdf',[img,scan],{}),('merge',[pdf,pdf],{}),('extract',[pdf],{'pages':'2,1'}),('rotate_pdf',[pdf],{'pages':'1'}),('split',[pdf],{}),('pdf_png',[pdf],{'dpi':150}),('text',[pdf],{}),('txt_pdf',[txt],{}),('ocr',[scan],{})]
    scanned=sorted(samples.glob('phase1-*/scanned-pdf-input/*.pdf'))
    if scanned:cases.append(('ocr',[scanned[-1]],{}))
    if word and has_word():cases.append(('docx_pdf',[word[-1]],{}))
    records=[]
    for index,(action,paths,options) in enumerate(cases):
        folder=output/f'{index+1:02d}-{action}';folder.mkdir()
        row={'action':action,'passed':False}
        try:
            files=run(action,paths,dict(options,folder=folder));assert files
            row['outputs']=[str(f) for f in files]
            for file in files:
                assert file.stat().st_size>0
                if file.suffix=='.pdf':
                    document=reader(file);assert len(document.pages)>0
                    if action=='docx_pdf':
                        assert len(document.pages)==2 and 'Microsoft Word' in document.pages[0].extract_text()
                        row['producer']=str(document.metadata.producer)
                    import pypdfium2 as pdfium
                    document=pdfium.PdfDocument(str(file))
                    try:
                        page=document[0];bitmap=page.render(scale=1)
                        try:bitmap.to_pil().save(folder/(file.stem+'-preview.png'))
                        finally:bitmap.close();page.close()
                    finally:document.close()
                elif file.suffix=='.txt':assert file.read_text(encoding='utf-8').strip()
                else:
                    from PIL import Image
                    with Image.open(file) as image:image.load()
            row['passed']=True
        except Exception:row['error']=traceback.format_exc()
        records.append(row)
        (output/'results.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
    unchanged=all(hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest for name,digest in hashes.items())
    (output/'summary.json').write_text(json.dumps({'passed':sum(r['passed'] for r in records),'total':len(records),'originals_unchanged':unchanged},indent=2),encoding='utf-8')
    return 0 if unchanged and all(r['passed'] for r in records) else 1
