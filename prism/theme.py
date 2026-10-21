"""Windows personalization, shared by native surfaces and custom-painted controls."""
import ctypes
import sys
from dataclasses import dataclass
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

@dataclass(frozen=True)
class Appearance:
    dark: bool
    background: str
    surface: str
    text: str
    muted: str
    border: str
    accent: str
    accent_text: str
    high_contrast: bool = False
    animations: bool = True
    transparency: bool = True


def tint(base,accent,amount):
    a,b=QColor(base),QColor(accent)
    return QColor(*[round(x*(1-amount)+y*amount) for x,y in zip(a.getRgb()[:3],b.getRgb()[:3])]).name()


def contrast_text(color):
    c=QColor(color)
    channels=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in (c.redF(),c.greenF(),c.blueF())]
    luminance=sum(a*b for a,b in zip(channels,(.2126,.7152,.0722)))
    return '#000000' if luminance>.179 else '#ffffff'


def appearance(choice='System'):
    app=QApplication.instance()
    dark=app.styleHints().colorScheme()==Qt.ColorScheme.Dark
    accent=app.palette().highlight().color().name()
    hc=False; animations=True; transparency=True
    colors=None
    if sys.platform=='win32':
        import winreg
        def read(key,name,default):
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER,key) as h: return winreg.QueryValueEx(h,name)[0]
            except OSError: return default
        key=r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize'
        dark=not bool(read(key,'AppsUseLightTheme',not dark))
        transparency=bool(read(key,'EnableTransparency',1))
        # DWM color is ARGB, unlike the BGR AccentColor registry entry.
        color=ctypes.c_uint(); opaque=ctypes.c_bool()
        if ctypes.windll.dwmapi.DwmGetColorizationColor(ctypes.byref(color),ctypes.byref(opaque))==0:
            accent=f'#{color.value & 0xffffff:06x}'
        class HIGHCONTRAST(ctypes.Structure):
            _fields_=[('cbSize',ctypes.c_uint),('dwFlags',ctypes.c_uint),('scheme',ctypes.c_wchar_p)]
        info=HIGHCONTRAST(); info.cbSize=ctypes.sizeof(info)
        if ctypes.windll.user32.SystemParametersInfoW(0x42,info.cbSize,ctypes.byref(info),0): hc=bool(info.dwFlags & 1)
        enabled=ctypes.c_int(1)
        if ctypes.windll.user32.SystemParametersInfoW(0x1042,0,ctypes.byref(enabled),0): animations=bool(enabled.value)
        def system_color(index):
            value=ctypes.windll.user32.GetSysColor(index)
            return QColor(value & 255,(value>>8)&255,(value>>16)&255).name()
        if hc: colors=[system_color(i) for i in (5,15,8,8,6,13,14)]
    if choice!='System': dark=choice=='Dark'
    values=colors or ([ '#10151c','#232d39','#edf3fc','#a9b9cc','#536071',accent,contrast_text(accent)] if dark else ['#f3f5f8','#ffffff','#192536','#53657b','#b6c6d9',accent,contrast_text(accent)])
    if not hc:
        values[0]=tint(values[0],accent,.08 if dark else .04)
        values[1]=tint(values[1],accent,.13 if dark else .07)
        values[4]=tint(values[4],accent,.25)
    return Appearance(dark,*values,hc,animations and not hc,transparency and not hc)


def stylesheet(t):
    return f'''
QWidget {{background:{t.background}; color:{t.text}; font-family:"Segoe UI"; font-size:12px;}}
QWidget#prismWheel {{background:transparent; border:0;}}
QLabel {{background:transparent;}}
QLabel#eyebrow {{color:{t.muted}; font-size:10px;}}
QLabel#brand {{font-size:18px;font-weight:600;}}
QLabel#brandMark {{background:{t.accent};border-radius:9px;}}
QLabel#sectionTitle {{font-weight:600;}}
QLabel#mutedSmall {{color:{t.muted};font-size:10px;}}
QFrame#divider {{background:{t.border};border:0;}}
QLabel#title {{font-size:18px; font-weight:650;}}
QLabel#muted {{color:{t.muted};}}
QFrame#card {{background:{tint(t.background,t.surface,.55)}; border:1px solid {t.border}; border-radius:16px;}}
QPushButton {{background:{t.surface}; border:1px solid {t.border}; padding:10px 16px; border-radius:8px; text-align:center;}}
QPushButton:hover {{background:{tint(t.surface,t.accent,.15) if not t.high_contrast else t.surface};}}
QPushButton:hover,QPushButton:focus,QComboBox:focus,QLineEdit:focus {{border:1px solid {t.accent};}}
QPushButton#primary {{border-radius:12px;}}
QPushButton:pressed,QPushButton#primary {{background:{t.accent}; color:{t.accent_text};}}
QPushButton {{outline:0;}}
QPushButton#compact {{padding:4px 10px;}}
QPushButton#iconButton {{padding:4px;background:transparent;border-color:transparent;}}
QPushButton#iconButton:hover,QPushButton#iconButton:focus {{border-color:{t.accent};}}
QPushButton#textButton {{padding:4px 0;background:transparent;border-color:transparent;color:{t.muted};font-size:10px;}}
QPushButton#textButton:focus {{border-color:{t.accent};}}
QPushButton#tool {{padding:0;}}
QPushButton:disabled {{color:{t.muted};}}
QListWidget,QPlainTextEdit {{background:{t.surface}; border:1px solid {t.border}; border-radius:8px; padding:8px;}}
QListWidget#fileList {{background:transparent;border:0;padding:0;outline:0;}}
QListWidget#fileList::item {{padding:0;border:0;background:transparent;}}
QListWidget::item:selected,QMenu::item:selected {{background:{t.accent}; color:{t.accent_text};}}
QProgressBar {{background:{t.surface}; border:0; border-radius:4px; height:7px;}}
QProgressBar::chunk {{background:{t.accent}; border-radius:4px;}}
QLineEdit,QSpinBox,QComboBox {{background:{t.surface}; border:1px solid {t.border}; padding:7px; border-radius:5px;}}
QMenu {{background:{t.surface}; border:1px solid {t.border};}}
QMenu::item {{padding:9px 24px;}}
QScrollBar:vertical {{background:{t.background};width:10px;margin:2px;}}
QScrollBar::handle:vertical {{background:{t.border};min-height:28px;border-radius:3px;}}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical {{height:0;}}
QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical {{background:transparent;}}
QCheckBox {{spacing:8px;}}
'''
