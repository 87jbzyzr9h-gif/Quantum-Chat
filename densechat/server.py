"""Loopback-only classical control interface for the trusted quantum simulator."""
import json
from pathlib import Path
import socketserver
import threading

from .session import ChatSession

MAX_LINE_BYTES = 30000
MAX_RESPONSE_BYTES = 3_000_000  # Last 100 maximum-size messages, including JSON escaping.
NAMES = ('Bumi', 'Mars')


def wire_json(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=True) + '\n').encode('utf-8')


class SimulatorServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, port: int = 8765, *, seed=20261106, noise=0.0, ack_noise=0.0, attempts=3, log: Path | None = None):
        self.session = ChatSession(seed, noise, ack_noise, attempts)
        for name in NAMES:
            self.session.add_endpoint(name)
        self.lock = threading.RLock()
        self.peers = {}
        self.control_received_bytes = self.control_sent_bytes = 0
        self.log = log
        if log:
            log.parent.mkdir(parents=True, exist_ok=True)
            with log.open('a', encoding='utf-8'):
                pass
        super().__init__(('127.0.0.1', port), PeerHandler)

    def broadcast(self, value: dict):
        with self.lock:
            for peer in list(self.peers.values()):
                peer.emit(value)

    def snapshot(self):
        return {**self.session.stats(), 'online': sorted(self.peers),
                'simulator_control_received_bytes': self.control_received_bytes,
                'simulator_control_sent_bytes': self.control_sent_bytes,
                'transport_note': 'TCP localhost carries CLASSICAL simulator commands/results. Counts are a snapshot before the current reply.'}


class PeerHandler(socketserver.StreamRequestHandler):
    def setup(self):
        super().setup()
        self.name = None
        self.output_lock = threading.Lock()

    def emit(self, value: dict):
        data = wire_json(value)
        try:
            with self.server.lock, self.output_lock:
                self.wfile.write(data)
                self.wfile.flush()
                self.server.control_sent_bytes += len(data)
            return True
        except (OSError, ValueError):
            return False

    def read_request(self):
        data = self.rfile.readline(MAX_LINE_BYTES + 1)
        with self.server.lock:
            self.server.control_received_bytes += len(data)
        if not data:
            return None
        if len(data) > MAX_LINE_BYTES or not data.endswith(b'\n'):
            raise ValueError('Permintaan terlalu panjang atau tanpa terminator')
        value = json.loads(data)
        if not isinstance(value, dict):
            raise ValueError('Permintaan harus berupa objek JSON')
        return value

    def handle(self):
        try:
            hello = self.read_request()
            if hello is None:
                return
            if set(hello) != {'action', 'name'} or hello['action'] != 'join' or hello['name'] not in NAMES:
                raise ValueError('Masuk dengan nama Bumi atau Mars')
            with self.server.lock:
                name = hello['name']
                if name in self.server.peers:
                    raise ValueError(f'{name} sudah tersambung')
                self.name = name
                self.server.peers[name] = self
                self.emit({'kind': 'welcome', 'name': name, 'online': sorted(self.server.peers),
                           'notice': 'LOCAL SIMULATION: TCP is classical control traffic, not a physical quantum channel.'})
                self.server.broadcast({'kind': 'system', 'text': f'{name} tersambung.'})
            while True:
                try:
                    request = self.read_request()
                    if request is None or request.get('action') == 'quit':
                        return
                    self.dispatch(request)
                except (ValueError, UnicodeError, TypeError) as error:
                    self.emit({'kind': 'error', 'text': str(error)})
        except (ValueError, TypeError, OSError) as error:
            self.emit({'kind': 'error', 'text': str(error)})
        finally:
            with self.server.lock:
                if self.name and self.server.peers.get(self.name) is self:
                    del self.server.peers[self.name]
                    self.server.broadcast({'kind': 'system', 'text': f'{self.name} terputus.'})

    def dispatch(self, request: dict):
        action = request.get('action')
        with self.server.lock:
            if action == 'stats':
                self.emit({'kind': 'stats', 'data': self.server.snapshot()})
            elif action == 'history':
                self.emit({'kind': 'history', 'messages': self.server.session.history[-100:]})
            elif action == 'send':
                if set(request) != {'action', 'text'} or not isinstance(request['text'], str):
                    raise ValueError('Kirim field text berupa string')
                other = next(name for name in NAMES if name != self.name)
                if other not in self.server.peers:
                    raise ValueError(f'{other} belum tersambung; buka terminal penerima terlebih dahulu')
                before = len(self.server.session.history)
                result = self.server.session.send(self.name, other, request['text'])
                if len(self.server.session.history) > before:
                    message = self.server.session.history[-1]
                    self.server.peers[other].emit({'kind': 'message', **message, 'verified': True})
                self.emit({'kind': 'receipt', 'sequence': result.sequence, 'status': result.status,
                           'attempts': result.attempts, 'resources': result.resources})
                if self.server.log:
                    try:
                        with self.server.log.open('a', encoding='utf-8') as log:
                            log.write(json.dumps(result.to_dict(), ensure_ascii=True) + '\n')
                    except OSError:
                        self.server.log = None
                        self.server.broadcast({'kind': 'system', 'text': 'Penulisan log gagal; logging dimatikan, sesi tetap berjalan.'})
            else:
                raise ValueError('Perintah tidak dikenal')
