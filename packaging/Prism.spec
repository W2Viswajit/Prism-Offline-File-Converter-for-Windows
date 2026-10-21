from pathlib import Path
from PyInstaller.utils.hooks import collect_all
root=Path(SPECPATH).parent
datas=[(str(root/'THIRD_PARTY.md'),'.')];binaries=[];hiddenimports=['win32com.client','win32timezone','pythoncom','pywintypes']
for package in ['rapidocr','pypdfium2']:
    d,b,h=collect_all(package);datas+=d;binaries+=b;hiddenimports+=h
# Preserve redistribution notices from the installed runtime distributions.
import importlib.metadata as metadata
for distribution in metadata.distributions():
    name=distribution.metadata.get('Name','dependency')
    for f in distribution.files or []:
        if any(token in f.name.lower() for token in ['license','copying','notice','copyright']) and not f.name.endswith(('.py','.pyc')):
            path=Path(distribution.locate_file(f))
            if path.is_file():datas.append((str(path),'licenses/'+name+'/'+str(f.parent).replace('..','_')))
a=Analysis([str(root/'main.py')],pathex=[str(root)],binaries=binaries,datas=datas,hiddenimports=hiddenimports,excludes=['pytest','tkinter','matplotlib','IPython'])
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,[],exclude_binaries=True,name='Prism',console=False,icon=str(root/'prism.ico'))
coll=COLLECT(exe,a.binaries,a.datas,strip=False,upx=False,name='Prism')
