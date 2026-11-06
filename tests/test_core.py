from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
import numpy as np
import qsimcirq

from densechat.protocol import ACK_SIZE, HEADER, InvalidFrame, decode_message, digest, encode_ack, encode_message, valid_ack
from densechat.quantum import QuantumChannel, encode_pair, joint_decode, transfer_qubit_a
from densechat.session import ChatSession, Endpoint


class QuantumTests(unittest.TestCase):
    def test_four_symbols_from_actual_joint_measurements(self):
        for phase in (0, 1):
            for flip in (0, 1):
                circuit = joint_decode(transfer_qubit_a(encode_pair(phase, flip)))
                result = qsimcirq.QSimSimulator(seed=10).run(circuit, repetitions=1)
                self.assertEqual(result.measurements['received'].tolist(), [[phase, flip]])

    def test_transfer_required(self):
        with self.assertRaises(PermissionError):
            joint_decode(encode_pair(1, 0))

    def test_all_byte_values_order_and_actual_noise(self):
        data = bytes(range(256))
        self.assertEqual(QuantumChannel(12).transmit(data), data)
        noisy = QuantumChannel(12, 0.05).transmit(data)
        self.assertNotEqual(noisy, data)
        self.assertEqual(noisy, QuantumChannel(12, 0.05).transmit(data))

    def test_only_one_shot_per_fresh_pair(self):
        with patch('densechat.quantum.qsimcirq.QSimSimulator') as simulator:
            simulator.return_value.run.return_value.measurements = {'received': np.array([[0, 0]])}
            QuantumChannel(1).transmit(b'ab')
            self.assertEqual(simulator.return_value.run.call_count, 8)
            self.assertTrue(all(c.kwargs['repetitions'] == 1 for c in simulator.return_value.run.call_args_list))


class ProtocolTests(unittest.TestCase):
    def test_utf8_empty_control_multiline_roundtrip(self):
        for text in ['', 'Hai! Apa kabarmu hari ini', '你好 🌍 مرحبا', 'a\0b\nbaris\tbaru', '/quit']:
            packet = decode_message(encode_message(text, 10))
            self.assertEqual(packet.text, text)
            self.assertEqual(packet.sequence, 10)

    def test_corruption_and_size_rejected(self):
        wire = encode_message('abc', 1)
        for offset in (0, HEADER.size, len(wire) - 1):
            broken = bytearray(wire)
            broken[offset] ^= 1
            with self.assertRaises(InvalidFrame):
                decode_message(bytes(broken))
        with self.assertRaises(InvalidFrame):
            decode_message(wire[:-1])
        with self.assertRaises(ValueError):
            encode_message('🙂' * 1025, 1)
        with self.assertRaises(ValueError):
            encode_message('a', 0)

    def test_bad_utf8_even_with_valid_checksum(self):
        body = HEADER.pack(b'SD', 1, 1, 1) + b'\xff'
        with self.assertRaises(InvalidFrame):
            decode_message(body + digest(body))

    def test_ack_binds_sequence_and_full_frame(self):
        wire = encode_message('hello', 1)
        ack = encode_ack(1, digest(wire), True)
        self.assertEqual(len(ack), ACK_SIZE)
        self.assertTrue(valid_ack(ack, 1, digest(wire)))
        self.assertFalse(valid_ack(ack, 2, digest(wire)))
        self.assertFalse(valid_ack(ack, 1, digest(wire + b'x')))
        self.assertFalse(valid_ack(ack[:-1], 1, digest(wire)))

    def test_deduplication_and_sequence_reuse(self):
        receiver = Endpoint()
        wire = encode_message('abc', 1)
        self.assertTrue(receiver.receive(wire)[1])
        self.assertFalse(receiver.receive(wire)[1])
        self.assertIsNone(receiver.receive(encode_message('other', 1))[0])


class SessionTests(unittest.TestCase):
    def make_session(self, **kwargs):
        session = ChatSession(**kwargs)
        session.add_endpoint('Bumi')
        session.add_endpoint('Mars')
        return session

    def test_two_way_actual_deliveries_and_resource_ledger(self):
        session = self.make_session()
        for sender, recipient, text in [('Bumi', 'Mars', 'Halo 🌏'), ('Mars', 'Bumi', 'Diterima!'), ('Bumi', 'Mars', '')]:
            result = session.send(sender, recipient, text)
            self.assertTrue(result.confirmed)
            self.assertEqual(result.received_text, text)
            frame_bytes = len(encode_message(text, result.sequence))
            self.assertEqual(result.resources['sent_a_qubits'], frame_bytes * 4)
            self.assertEqual(result.resources['distributed_b_qubits'], frame_bytes * 4)
            self.assertEqual(result.resources['classical_ack_bits'], ACK_SIZE * 8)
        self.assertEqual(len(session.history), 3)

    def test_ack_lost_retries_do_not_duplicate(self):
        session = self.make_session(ack_noise=1, attempts=3)
        result = session.send('Bumi', 'Mars', 'received, acknowledgement lost')
        self.assertTrue(result.received)
        self.assertFalse(result.confirmed)
        self.assertEqual(result.attempts, 3)
        self.assertEqual(len(session.history), 1)
        self.assertEqual(result.resources['classical_ack_bits'], 3 * ACK_SIZE * 8)
        self.assertEqual(result.resources['sent_a_qubits'], len(encode_message('received, acknowledgement lost', 1)) * 4 * 3)

    def test_total_quantum_noise_never_displays_original_as_guess(self):
        session = self.make_session(noise=1, attempts=2)
        result = session.send('Bumi', 'Mars', 'should not be guessed')
        self.assertFalse(result.received)
        self.assertFalse(result.confirmed)
        self.assertIsNone(result.received_text)
        self.assertEqual(session.history, [])

    def test_damage_then_retry_recovers(self):
        session = self.make_session(attempts=2)
        original = session.channel.transmit
        calls = []

        def transmit(wire):
            measured = original(wire)
            calls.append(1)
            return bytes([measured[0] ^ 1]) + measured[1:] if len(calls) == 1 else measured

        with patch.object(session.channel, 'transmit', side_effect=transmit):
            result = session.send('Mars', 'Bumi', 'retry recovery')
        self.assertTrue(result.confirmed)
        self.assertEqual(result.attempts, 2)
        self.assertEqual(len(session.history), 1)

    def test_invalid_send_consumes_no_resource(self):
        session = self.make_session()
        with self.assertRaises(ValueError):
            session.send('Bumi', 'Mars', 'x' * 4097)
        self.assertEqual(session.sequence, 0)
        self.assertEqual(session.stats()['resources']['sent_a_qubits'], 0)

    def test_demo_two_way_slash_empty_and_terminal_escaping(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run([sys.executable, str(root / 'chat.py'), '--demo'], cwd=root,
                                input='Halo 🌍\n/as Mars\nBalasan\n/send /quit\n\n/history\n/stats\n/quit\n',
                                text=True, capture_output=True, timeout=20, check=True)
        self.assertIn('Bumi → Mars #1', result.stdout)
        self.assertIn('Mars → Bumi #2', result.stdout)
        self.assertIn('/quit', result.stdout)
        self.assertIn('"messages_received": 4', result.stdout)
        from densechat.cli import visible
        self.assertEqual(visible('\x1b[31m'), '\\x1b[31m')


if __name__ == '__main__':
    unittest.main()
