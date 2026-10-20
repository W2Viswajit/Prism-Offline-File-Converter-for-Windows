"""One Prism process per Windows user; Explorer launches forward file paths."""
import hashlib
import json
from pathlib import Path
from PySide6.QtCore import QObject,Signal,QLockFile,QStandardPaths
from PySide6.QtNetwork import QLocalServer,QLocalSocket

class Instance(QObject):
    received=Signal(list)
    def __init__(self,parent=None):
        super().__init__(parent)
        self.name='Prism-'+hashlib.sha256(str(Path.home()).encode()).hexdigest()[:20]
        lock_dir=Path(QStandardPaths.writableLocation(QStandardPaths.TempLocation))
        self.lock=QLockFile(str(lock_dir/(self.name+'.lock')))
        self.lock.setStaleLockTime(0)
        self.server=QLocalServer(self)
        self.server.setSocketOptions(QLocalServer.UserAccessOption)
        self.server.newConnection.connect(self.accept)
        self.connections={}
    def forward(self,paths):
        # Windows permits multiple named-pipe listeners with the same name.
        # QLockFile, not listen(), elects the primary process atomically.
        if self.lock.tryLock(0):
            if not self.server.listen(self.name):
                self.lock.unlock()
                raise RuntimeError('Could not start the Prism file-launch listener.')
            return False
        socket=QLocalSocket(self)
        import time
        for attempt in range(30):
            socket.connectToServer(self.name)
            if socket.waitForConnected(100): break
            socket.abort(); time.sleep(.1)
        else:
            raise RuntimeError('Another Prism instance is starting but could not be reached. Try again.')
        payload=json.dumps([str(Path(p).resolve()) for p in paths]).encode()+b'\n'
        socket.write(payload)
        if socket.bytesToWrite() and not socket.waitForBytesWritten(3000): raise RuntimeError('Could not send files to the running Prism instance.')
        socket.disconnectFromServer()
        return True
    def start(self):
        # Drain connections queued while the main window was being created.
        self.accept()
    def accept(self):
        while self.server.hasPendingConnections():
            socket=self.server.nextPendingConnection(); self.connections[socket]=bytearray()
            socket.readyRead.connect(lambda s=socket:self.read(s))
            socket.disconnected.connect(lambda s=socket:self.cleanup(s))
            self.read(socket)
    def cleanup(self,socket):
        self.connections.pop(socket,None); socket.deleteLater()
    def read(self,socket):
        buffer=self.connections.get(socket)
        if buffer is None: return
        buffer.extend(bytes(socket.readAll()))
        if len(buffer)>1024*1024: socket.abort(); return
        if b'\n' not in buffer: return
        try:
            paths=json.loads(bytes(buffer).split(b'\n',1)[0])
            if isinstance(paths,list) and all(isinstance(p,str) for p in paths): self.received.emit(paths)
        except (ValueError,UnicodeError): pass
        socket.disconnectFromServer()
