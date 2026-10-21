# Third-party dependencies

Prism uses Python, PySide6/Qt, Pillow, pypdf, pypdfium2/PDFium, ReportLab and pywin32. Offline OCR uses RapidOCR, ONNX Runtime and their dependencies/models. Microsoft Word or LibreOffice may be used from an existing local installation; neither is bundled.

Dependencies retain their respective copyrights and license terms. The installer build collects dependency license and notice files into the application's `_internal/licenses` directory. Review applicable library, runtime and model licenses before redistribution; this list is not a legal compliance audit.

Build tools: PyInstaller and Inno Setup. See [packaging instructions](packaging/README.md) for release requirements.
