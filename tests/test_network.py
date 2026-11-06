import json
from pathlib import Path
import socket
import subprocess
import sys
import threading
import unittest

from densechat.server import MAX_RESPONSE_BYTES, SimulatorServer, wire_json


class Peer:
    def __init__(self, port, name):
        self.socket = socket.create_connection(('127.0.0.1', port), timeout=5)
        self.reader = self.socket.makefile('rb')
        self.send({'action': 'join', 'name': name})

    def send(self, value):
        self.socket.sendall(wire_json(value))

    def event(self, kind):
        for _ in range(20):
            line = self.reader.readline(MAX_RESPONSE_BYTES + 1)
            if not line:
                raise AssertionError('Server disconnected unexpectedly')
            event = json.loads(line)
            if event['kind'] == kind:
                return event
        raise AssertionError(f'Missing event: {kind}')

    def close(self):
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.reader.close()
        self.socket.close()


class NetworkTests(unittest.TestCase):
    def setUp(self):
        self.server = SimulatorServer(0)
        self.thread = threading.Thread(target=lambda: self.server.serve_forever(poll_interval=0.02), daemon=True)
        self.thread.start()
        self.port = self.server.server_address[1]
        self.peers = []

    def tearDown(self):
        for peer in self.peers:
            peer.close()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def peer(self, name):
        peer = Peer(self.port, name)
        self.peers.append(peer)
        return peer

    def test_two_actual_clients_send_both_directions(self):
        bumi, mars = self.peer('Bumi'), self.peer('Mars')
        self.assertEqual(bumi.event('welcome')['name'], 'Bumi')
        self.assertEqual(mars.event('welcome')['name'], 'Mars')
        for sender, recipient, text in [(bumi, mars, 'Halo Mars 🚀'), (mars, bumi, 'Balasan ke Bumi 你好')]:
            sender.send({'action': 'send', 'text': text})
            message = recipient.event('message')
            self.assertEqual(message['text'], text)
            self.assertTrue(message['verified'])
            receipt = sender.event('receipt')
            self.assertEqual(receipt['status'], 'CONFIRMED')
            self.assertNotIn('received_text', receipt)
        bumi.send({'action': 'stats'})
        stats = bumi.event('stats')['data']
        self.assertEqual(stats['messages_received'], 2)
        self.assertGreater(stats['simulator_control_received_bytes'], 0)
        self.assertGreater(stats['simulator_control_sent_bytes'], 0)

    def test_no_receiver_does_not_consume_qubits(self):
        bumi = self.peer('Bumi')
        bumi.event('welcome')
        bumi.send({'action': 'send', 'text': 'waiting'})
        self.assertIn('belum tersambung', bumi.event('error')['text'])
        self.assertEqual(self.server.session.sequence, 0)

    def test_duplicate_identity_is_rejected_without_disconnect_of_original(self):
        one = self.peer('Bumi')
        one.event('welcome')
        duplicate = self.peer('Bumi')
        self.assertIn('sudah tersambung', duplicate.event('error')['text'])
        one.send({'action': 'stats'})
        self.assertEqual(one.event('stats')['data']['online'], ['Bumi'])

    def test_invalid_request_then_healthy_connection(self):
        bumi = self.peer('Bumi')
        bumi.event('welcome')
        bumi.send({'action': 'send', 'text': ['invalid']})
        self.assertEqual(bumi.event('error')['kind'], 'error')
        bumi.send({'action': 'stats'})
        self.assertEqual(bumi.event('stats')['data']['messages_attempted'], 0)

    def test_large_history_response_preserves_frame_boundaries(self):
        bumi = self.peer('Bumi')
        bumi.event('welcome')
        with self.server.lock:
            self.server.session.history = [{'sequence': i, 'sender': 'Bumi', 'recipient': 'Mars', 'text': '\0' * 4096}
                                           for i in range(1, 4)]
        bumi.send({'action': 'history'})
        messages = bumi.event('history')['messages']
        self.assertEqual(len(messages), 3)
        self.assertTrue(all(len(m['text']) == 4096 for m in messages))

    def test_real_terminal_client_program(self):
        mars = self.peer('Mars')
        mars.event('welcome')
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run([sys.executable, str(root/'chat.py'), '--name', 'Bumi', '--port', str(self.port)],
                                cwd=root, input='Dari client terminal 🌍\n/stats\n/quit\n', text=True,
                                capture_output=True, timeout=20, check=True)
        self.assertIn('CONFIRMED', result.stdout)
        self.assertEqual(mars.event('message')['text'], 'Dari client terminal 🌍')


if __name__ == '__main__':
    unittest.main()
