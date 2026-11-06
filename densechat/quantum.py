"""Trusted quantum backend. Only measured symbols cross its output boundary."""
from dataclasses import dataclass
import cirq
import qsimcirq


@dataclass(frozen=True, slots=True)
class EncodedAtSender:
    circuit: cirq.FrozenCircuit


@dataclass(frozen=True, slots=True)
class ArrivedAtReceiver:
    circuit: cirq.FrozenCircuit


def encode_pair(phase: int, flip: int) -> EncodedAtSender:
    if phase not in (0, 1) or flip not in (0, 1):
        raise ValueError('Encoding requires two bits')
    a, b = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(cirq.H(a), cirq.CNOT(a, b))
    if phase:
        circuit.append(cirq.Z(a))
    if flip:
        circuit.append(cirq.X(a))
    return EncodedAtSender(circuit.freeze())


def transfer_qubit_a(pair: EncodedAtSender, noise: float = 0) -> ArrivedAtReceiver:
    """Quantum-channel ownership transition in the model, not a network API."""
    if not isinstance(pair, EncodedAtSender) or not 0 <= noise <= 1:
        raise ValueError('An encoded pair and a valid noise probability are required')
    circuit = cirq.Circuit(pair.circuit)
    if noise:
        circuit.append(cirq.depolarize(noise)(cirq.LineQubit(0)), strategy=cirq.InsertStrategy.NEW)
    return ArrivedAtReceiver(circuit.freeze())


def joint_decode(pair: ArrivedAtReceiver) -> cirq.Circuit:
    if not isinstance(pair, ArrivedAtReceiver):
        raise PermissionError('Receiver needs transferred A before joint decoding')
    a, b = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(pair.circuit)
    circuit.append(cirq.CNOT(a, b), strategy=cirq.InsertStrategy.NEW)
    circuit.append(cirq.H(a), strategy=cirq.InsertStrategy.NEW)
    circuit.append(cirq.measure(a, b, key='received'), strategy=cirq.InsertStrategy.NEW)
    return circuit


class QuantumChannel:
    def __init__(self, seed: int, noise: float = 0):
        self.simulator = qsimcirq.QSimSimulator(seed=seed, qsim_options={'t': 1},
                                               circuit_memoization_size=4)
        self.circuits = {(phase, flip): joint_decode(transfer_qubit_a(encode_pair(phase, flip), noise))
                         for phase in (0, 1) for flip in (0, 1)}

    def transmit(self, frame: bytes) -> bytes:
        received = bytearray()
        for byte in frame:
            decoded_byte = 0
            for shift in (6, 4, 2, 0):
                two_bits = (byte >> shift) & 3
                result = self.simulator.run(self.circuits[two_bits >> 1, two_bits & 1], repetitions=1)
                phase, flip = map(int, result.measurements['received'][0])
                decoded_byte = (decoded_byte << 2) | (phase << 1) | flip
            received.append(decoded_byte)
        return bytes(received)
