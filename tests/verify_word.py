def main():
    """Native Microsoft Word integration check, with a disposable DOCX fixture."""
    import sys,zipfile,hashlib,json
    from pathlib import Path
    from datetime import datetime
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from prism.engine import run,has_word,reader
    import pypdfium2 as pdfium
    assert has_word(), 'Microsoft Word is not registered on this computer'
    folder=Path(__file__).resolve().parents[1]/'samples'/('word-demo-'+datetime.now().strftime('%Y%m%d-%H%M%S'));folder.mkdir()
    source=folder/'Prism Word sample.docx'
    content_types='''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>'''
    relationships='''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'''
    document='''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:rPr><w:b/><w:color w:val="286050"/><w:sz w:val="44"/></w:rPr><w:t>Prism - Microsoft Word export</w:t></w:r></w:p><w:p><w:r><w:t>This PDF is exported by Microsoft Word on Windows.</w:t></w:r></w:p><w:p><w:r><w:t>The source DOCX is opened read-only and stays unchanged.</w:t></w:r></w:p><w:tbl><w:tblPr><w:tblW w:w="9000" w:type="dxa"/><w:tblBorders><w:top w:val="single" w:sz="8"/><w:left w:val="single" w:sz="8"/><w:bottom w:val="single" w:sz="8"/><w:right w:val="single" w:sz="8"/><w:insideH w:val="single" w:sz="8"/><w:insideV w:val="single" w:sz="8"/></w:tblBorders></w:tblPr><w:tblGrid><w:gridCol w:w="4500"/><w:gridCol w:w="4500"/></w:tblGrid><w:tr><w:tc><w:tcPr><w:tcW w:w="4500" w:type="dxa"/></w:tcPr><w:p><w:r><w:t>Feature</w:t></w:r></w:p></w:tc><w:tc><w:tcPr><w:tcW w:w="4500" w:type="dxa"/></w:tcPr><w:p><w:r><w:t>Expected result</w:t></w:r></w:p></w:tc></w:tr><w:tr><w:tc><w:p><w:r><w:t>Table and page break</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>Preserved</w:t></w:r></w:p></w:tc></w:tr></w:tbl><w:p><w:r><w:br w:type="page"/></w:r></w:p><w:p><w:r><w:rPr><w:b/><w:sz w:val="32"/></w:rPr><w:t>Page 2 - Review the result</w:t></w:r></w:p><w:p><w:r><w:t>Native Word layout, embedded text, and two pages.</w:t></w:r></w:p><w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/></w:sectPr></w:body></w:document>'''
    with zipfile.ZipFile(source,'x',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml',content_types);z.writestr('_rels/.rels',relationships);z.writestr('word/document.xml',document)
    before=hashlib.sha256(source.read_bytes()).hexdigest()
    output=run('docx_pdf',[source])[0]
    assert hashlib.sha256(source.read_bytes()).hexdigest()==before
    pdf=reader(output);assert len(pdf.pages)==2
    assert 'Microsoft Word' in pdf.pages[0].extract_text()
    assert 'Page 2' in pdf.pages[1].extract_text()
    render=pdfium.PdfDocument(str(output))
    try:
        for index in range(len(render)):
            page=render[index];bitmap=page.render(scale=1.3)
            try:bitmap.to_pil().save(folder/f'word-page-{index+1}.png')
            finally:bitmap.close();page.close()
    finally:render.close()
    report={'backend':'Microsoft Word','pages':2,'original_unchanged':True,'output':str(output),'producer':str(pdf.metadata.producer)}
    (folder/'results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__': main()
