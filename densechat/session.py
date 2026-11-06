"""One chat session, two endpoints, fresh Bell pairs and bounded retries."""
from dataclasses import asdict, dataclass
import numpy as np
from .protocol import InvalidFrame, decode_message, digest, encode_ack, encode_message, valid_ack
from .quantum import QuantumChannel


@dataclass
class Resources:
    frame_bits: int = 0
    bell_pairs: int = 0
    sent_a_qubits: int = 0
    distributed_b_qubits: int = 0
    classical_ack_bits: int = 0

    def to_dict(self):
        return {**asdict(self), 'total_quantum_transfers': self.sent_a_qubits + self.distributed_b_qubits,
                'model_forward_classical_bits': 0}


class Endpoint:
    """Accepts measured frame bytes only; never receives sender text or operations."""
    def __init__(self):
        self.accepted = {}

    def receive(self, wire: bytes):
        try:
            packet = decode_message(wire)
            previous = self.accepted.get(packet.sequence)
            if previous is not None and previous != packet.fingerprint:
                raise InvalidFrame('Sequence sudah dipakai untuk pesan berbeda')
            if previous is None and len(self.accepted) >= 10000:
                raise InvalidFrame('Sesi penuh; mulai sesi server/demo baru')
            fresh = previous is None
            self.accepted[packet.sequence] = packet.fingerprint
            return packet, fresh, encode_ack(packet.sequence, packet.fingerprint, True), None
        except InvalidFrame as error:
            return None, False, encode_ack(), str(error)


@dataclass(frozen=True)
class Delivery:
    sequence: int
    sender: str
    recipient: str
    status: str
    confirmed: bool
    received: bool
    received_text: str | None
    attempts: int
    resources: dict
    events: tuple[dict, ...]

    def to_dict(self):
        return asdict(self)


class ChatSession:
    def __init__(self, seed: int = 20261106, noise: float = 0, ack_noise: float = 0, attempts: int = 3):
        if seed < 0 or not 0 <= noise <= 1 or not 0 <= ack_noise <= 1 or not 1 <= attempts <= 20:
            raise ValueError('Seed, peluang noise, atau batas attempts tidak valid')
        quantum_seed, ack_seed = np.random.SeedSequence(seed).spawn(2)
        self.channel = QuantumChannel(int(quantum_seed.generate_state(1)[0]), noise)
        self.ack_rng = np.random.default_rng(ack_seed)
        self.noise, self.ack_noise, self.max_attempts = noise, ack_noise, attempts
        self.endpoints, self.history, self.sequence = {}, [], 0
        self.totals = Resources()

    def add_endpoint(self, name: str):
        if name in self.endpoints:
            raise ValueError('Nama sudah dipakai dalam sesi ini')
        self.endpoints[name] = Endpoint()

    def _return_ack(self, ack: bytes) -> bytes:
        if not self.ack_noise:
            return ack
        bits = np.unpackbits(np.frombuffer(ack, dtype=np.uint8))
        flips = (self.ack_rng.random(len(bits)) < self.ack_noise).astype(np.uint8)
        return np.packbits(bits ^ flips).tobytes()

    def send(self, sender: str, recipient: str, text: str) -> Delivery:
        if sender == recipient or sender not in self.endpoints or recipient not in self.endpoints:
            raise ValueError('Pengirim dan penerima harus dua endpoint sesi yang berbeda')
        # Validate before consuming a sequence or any quantum resource.
        wire = encode_message(text, self.sequence + 1)
        self.sequence += 1
        usage, events, received_text = Resources(), [], None
        was_received, confirmed = False, False
        for attempt in range(1, self.max_attempts + 1):
            pairs = len(wire) * 4
            usage.frame_bits += len(wire) * 8
            usage.bell_pairs += pairs
            usage.sent_a_qubits += pairs
            usage.distributed_b_qubits += pairs
            measured_wire = self.channel.transmit(wire)
            packet, fresh, ack, error = self.endpoints[recipient].receive(measured_wire)
            usage.classical_ack_bits += len(ack) * 8
            returned_ack = self._return_ack(ack)
            acknowledged = valid_ack(returned_ack, self.sequence, digest(wire))
            if packet is not None:
                was_received, received_text = True, packet.text
                if fresh:
                    self.history.append({'sequence': packet.sequence, 'sender': sender,
                                         'recipient': recipient, 'text': packet.text})
            events.append({'attempt': attempt, 'accepted': packet is not None,
                           'fresh': fresh, 'ack_valid': acknowledged, 'error': error})
            # Stop-and-wait sender consults only the returned classical ACK.
            if acknowledged:
                confirmed = True
                break
        for key, value in asdict(usage).items():
            setattr(self.totals, key, getattr(self.totals, key) + value)
        return Delivery(self.sequence, sender, recipient, 'CONFIRMED' if confirmed else 'UNCONFIRMED',
                        confirmed, was_received, received_text, attempt, usage.to_dict(), tuple(events))

    def stats(self):
        return {'messages_attempted': self.sequence, 'messages_received': len(self.history),
                'resources': self.totals.to_dict(), 'noise_per_a_qubit': self.noise,
                'ack_bit_error_rate': self.ack_noise, 'max_attempts': self.max_attempts,
                'note': 'Sumber daya model quantum; transport simulator klasik dihitung terpisah'}
