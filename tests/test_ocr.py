"""Optional integration check: the bundled sample must OCR without a network."""
import socket
import sys
from pathlib import Path
from threading import Event
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def test_ocr_sample_offline(monkeypatch):
    pytest.importorskip('rapidocr')
    pytest.importorskip('onnxruntime')
    from prism.engine import ocr
    def refuse_network(*args, **kwargs):
        raise AssertionError('OCR must not need network access after installation')
    monkeypatch.setattr(socket.socket, 'connect', refuse_network)
    sample = Path(__file__).resolve().parents[1] / 'samples' / 'sample-scan.png'
    assert ocr(sample, Event()).splitlines() == [
        'Prism makes file conversion simple.',
        'Review extracted text before using it.',
    ]
