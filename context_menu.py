"""Per-user classic Explorer menu registration. No administrator rights needed."""
from pathlib import Path
import sys

EXTENSIONS=('.png','.jpg','.jpeg','.webp','.bmp','.tif','.tiff','.pdf','.txt','.docx')
VERB='Prism.Open'
OWNER='PrismWindowsSourceApp'

def command_for(pythonw,main):
    # Shell directly invokes pythonw. Never route filenames through cmd.exe.
    for p in (pythonw,main):
        if '"' in str(p): raise ValueError('Invalid quote in application path.')
    return f'"{pythonw}" "{main}" "%1"'

def registry_keys():
    return [rf'Software\Classes\SystemFileAssociations\{ext}\shell\{VERB}' for ext in EXTENSIONS]

def owned(reg,key):
    try:
        with reg.OpenKey(reg.HKEY_CURRENT_USER,key) as handle:
            try: return reg.QueryValueEx(handle,'PrismOwner')[0]==OWNER
            except FileNotFoundError: return False
    except FileNotFoundError: return True

def install(reg,root):
    pythonw=root/'.venv'/'Scripts'/'pythonw.exe'; main=root/'main.py'
    if not pythonw.is_file() or not main.is_file():
        raise RuntimeError('Extract the whole ZIP and run Setup.bat successfully before installing the menu.')
    keys=registry_keys()
    if any(not owned(reg,key) for key in keys): raise RuntimeError('An existing menu entry has a different owner. No entries were changed.')
    command=command_for(pythonw,main)
    for key in keys:
        with reg.CreateKey(reg.HKEY_CURRENT_USER,key) as handle:
            reg.SetValueEx(handle,'',0,reg.REG_SZ,'Open with Prism')
            reg.SetValueEx(handle,'PrismOwner',0,reg.REG_SZ,OWNER)
            reg.SetValueEx(handle,'MultiSelectModel',0,reg.REG_SZ,'Single')
            reg.SetValueEx(handle,'Icon',0,reg.REG_SZ,str(root/'prism.ico'))
        with reg.CreateKey(reg.HKEY_CURRENT_USER,key+r'\command') as handle:
            reg.SetValueEx(handle,'',0,reg.REG_SZ,command)

def uninstall(reg):
    for key in registry_keys():
        if not owned(reg,key): continue
        for target in (key+r'\command',key):
            try: reg.DeleteKey(reg.HKEY_CURRENT_USER,target)
            except FileNotFoundError: pass

def main():
    if sys.platform!='win32': raise SystemExit('Menu registration is supported only on Windows.')
    import winreg
    import ctypes
    action=sys.argv[1] if len(sys.argv)>1 else 'install'
    try:
        if action=='install':
            install(winreg,Path(__file__).resolve().parent)
            print('Installed for your Windows user. Right-click ONE supported file > Show more options > Open with Prism.')
            print('Keep this Prism folder in place. Run the installer again if you move it.')
        elif action=='uninstall': uninstall(winreg); print('Prism right-click entries removed.')
        else: raise ValueError('Use install or uninstall.')
        ctypes.windll.shell32.SHChangeNotify(0x08000000,0,None,None)
    except Exception as e: print(f'Menu setup failed: {e}'); raise SystemExit(1)

if __name__=='__main__':main()
