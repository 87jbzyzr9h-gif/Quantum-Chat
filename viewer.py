"""Observer-only terminal viewer for the active superdense chat engine."""
import argparse
from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
import sys
import time

import cirq
import numpy as np
import qsimcirq

from densechat.protocol import HEADER, InvalidFrame, decode_message, encode_message
from densechat.quantum import QuantumChannel, encode_pair, joint_decode, transfer_qubit_a

A, B = cirq.LineQubit.range(2)
LABELS = ('00', '01', '10', '11')


@dataclass(frozen=True)
class Stage:
    title: str
    detail: str
    owner_a: str
    owner_b: str
    circuit: cirq.FrozenCircuit


def build_stages(bits: str, noise: float = 0.0) -> tuple[list[Stage], cirq.Circuit]:
    """Use engine circuits, inserting observer milestones without extra gates."""
    if bits not in LABELS or not 0 <= noise <= 1:
        raise ValueError('Dua bit 00/01/10/11 dan peluang noise [0,1] diperlukan')
    phase, flip = map(int, bits)
    encoded = encode_pair(phase, flip)
    arrived = transfer_qubit_a(encoded, noise)
    complete = joint_decode(arrived)
    circuit = cirq.Circuit()
    stages = [Stage('RESET', 'Pasangan baru dimulai pada |00>.', 'Bumi', 'Bumi', circuit.freeze())]

    def append_stage(title, detail, owner_a='Bumi', owner_b='Mars'):
        stages.append(Stage(title, detail, owner_a, owner_b, circuit.freeze()))

    # The engine prepares H and CNOT before any encoding operation.
    preparation = list(encoded.circuit.all_operations())
    circuit.append(preparation[0], strategy=cirq.InsertStrategy.NEW)
    append_stage('H(A)', 'A dalam superposisi; B masih |0>.', owner_b='Bumi')
    circuit.append(preparation[1], strategy=cirq.InsertStrategy.NEW)
    append_stage('CNOT(A,B): BELL PAIR', 'Dua qubit kini berada pada Bell state.', owner_b='Bumi')
    append_stage('DISTRIBUSI B', 'B dipindahkan ke Mars dalam model. State global tetap sama.')
    if phase:
        circuit.append(next(op for op in preparation[2:] if op.gate == cirq.Z), strategy=cirq.InsertStrategy.NEW)
    append_stage('ENCODE PHASE', f'Bit fase={phase}: ' + ('Z(A).' if phase else 'identitas, tidak ada gate Z.'))
    if flip:
        circuit.append(next(op for op in preparation[2:] if op.gate == cirq.X), strategy=cirq.InsertStrategy.NEW)
    append_stage('ENCODE FLIP', f'Bit flip={flip}: ' + ('X(A).' if flip else 'identitas, tidak ada gate X.'))
    if tuple(circuit.all_operations()) != tuple(encoded.circuit.all_operations()):
        raise RuntimeError('Viewer prefix differs from the active encoding engine')
    circuit = cirq.Circuit(arrived.circuit)
    append_stage('TRANSFER A', f'A tiba di Mars; depolarisasi transit p={noise:g}.', owner_a='Mars')
    # Last three moments are the active engine's CNOT, H, and measurement.
    circuit.append(complete[-3], strategy=cirq.InsertStrategy.NEW)
    append_stage('DECODE: CNOT(A,B)', 'Mars sudah memiliki A dan B; joint decoding diperbolehkan.', owner_a='Mars')
    circuit.append(complete[-2], strategy=cirq.InsertStrategy.NEW)
    append_stage('DECODE: H(A)', 'Probabilitas berikut adalah peluang hasil pengukuran dua bit.', owner_a='Mars')
    return stages, complete


def reduced_states(rho: np.ndarray):
    tensor = rho.reshape(2, 2, 2, 2)
    return (np.trace(tensor, axis1=1, axis2=3), np.trace(tensor, axis1=0, axis2=2))


def summary(rho: np.ndarray) -> dict:
    rho_a, rho_b = reduced_states(rho)

    def local(matrix):
        return {'p0': float(np.real(matrix[0, 0])), 'p1': float(np.real(matrix[1, 1])),
                'bloch': [float(2 * matrix[0, 1].real), float(-2 * matrix[0, 1].imag),
                          float((matrix[0, 0] - matrix[1, 1]).real)],
                'purity': float(np.trace(matrix @ matrix).real)}

    return {'probabilities': np.real(np.diag(rho)).clip(0, 1).tolist(),
            'global_purity': float(np.trace(rho @ rho).real), 'A': local(rho_a), 'B': local(rho_b)}


def complex_text(number: complex) -> str:
    real = 0.0 if abs(number.real) < 1e-7 else number.real
    imag = 0.0 if abs(number.imag) < 1e-7 else number.imag
    if imag == 0:
        return f'{real: .3f}'
    return f'{real: .3f}{imag:+.3f}j'


def density_rows(rho):
    return ['  [' + '  '.join(complex_text(value) for value in row) + ']' for row in rho]


def state_record(stage: Stage, seed: int) -> dict:
    # DensityMatrixSimulator displays the exact ensemble for noise, never a
    # pure-state trajectory mislabeled as the whole mixed state.
    circuit = cirq.Circuit(stage.circuit)
    rho = cirq.DensityMatrixSimulator(dtype=np.complex128).simulate(
        circuit, qubit_order=[A, B]).final_density_matrix
    state = None
    if cirq.has_unitary(circuit):
        vector = qsimcirq.QSimSimulator(seed=seed, qsim_options={'t': 1}).simulate(
            circuit, qubit_order=[A, B]).final_state_vector
        state = cirq.dirac_notation(vector, decimals=3)
    return {'title': stage.title, 'detail': stage.detail,
            'ownership': {'A': stage.owner_a, 'B': stage.owner_b},
            'circuit': str(circuit), 'state_vector_notation': state,
            'density_matrix': [[[float(v.real), float(v.imag)] for v in row] for row in rho],
            **summary(rho)}


def trace_pair(bits: str, noise: float, seed: int, shots: int) -> dict:
    stages, circuit = build_stages(bits, noise)
    records = [state_record(stage, seed) for stage in stages]
    simulator = qsimcirq.QSimSimulator(seed=seed, qsim_options={'t': 1}, circuit_memoization_size=1)
    histogram = Counter()
    first = None
    for _ in range(shots):
        measured = simulator.run(circuit, repetitions=1).measurements['received'][0]
        received = ''.join(map(str, map(int, measured)))
        if first is None:
            first = received
        histogram[received] += 1
    collapsed = np.zeros((4, 4), dtype=np.complex128)
    collapsed[int(first, 2), int(first, 2)] = 1
    records.append({'title': 'MEASURE A,B', 'detail': 'Satu hasil shot pertama; state bersyarat setelah pengukuran.',
                    'ownership': {'A': 'Mars', 'B': 'Mars'}, 'circuit': str(circuit),
                    'state_vector_notation': f'|{first}⟩',
                    'density_matrix': [[[float(v.real), float(v.imag)] for v in row] for row in collapsed],
                    **summary(collapsed)})
    return {'input_bits': bits, 'noise': noise, 'seed': seed, 'shots': shots,
            'first_measurement': first, 'histogram': {key: histogram[key] for key in LABELS},
            'stages': records, 'complete_circuit': str(circuit)}


def show_record(record: dict, number: int, total: int):
    print(f'\n[{number:02d}/{total:02d}] {record["title"]}\n{record["detail"]}')
    print(f'Lokasi: A={record["ownership"]["A"]}, B={record["ownership"]["B"]}')
    print(record['circuit'] or '(belum ada gate)')
    if record['state_vector_notation'] is not None:
        print('State global:', record['state_vector_notation'])
    else:
        print('State global campuran: tidak ada satu state-vector untuk seluruh ensemble.')
    print(f'Global purity={record["global_purity"]:.4f}')
    for label, probability in zip(LABELS, record['probabilities']):
        filled = round(probability * 24)
        print(f'  |{label}>  [{"#" * filled}{"." * (24 - filled)}] {probability:7.2%}')
    for name in ('A', 'B'):
        local = record[name]
        bloch = ', '.join(f'{x:+.3f}' for x in local['bloch'])
        print(f'  Lokal {name}: P(0)={local["p0"]:.2%}, P(1)={local["p1"]:.2%}; Bloch=({bloch}); purity={local["purity"]:.3f}')
    rho = np.asarray([[complex(*value) for value in row] for row in record['density_matrix']])
    print('Density matrix global, urutan |00>, |01>, |10>, |11>:')
    print('\n'.join(density_rows(rho)), flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument('--bits', choices=LABELS, help='Visualize one chosen two-bit symbol')
    source.add_argument('--all-symbols', action='store_true')
    source.add_argument('--message', help='Trace selected pairs from a UTF-8 message')
    parser.add_argument('--scope', choices=('payload', 'frame'), default='payload')
    parser.add_argument('--start', type=int, default=0, help='Zero-based pair index within selected scope')
    parser.add_argument('--pairs', type=int, default=4, help='Maximum pairs to display (1..32)')
    parser.add_argument('--noise', type=float, default=0)
    parser.add_argument('--shots', type=int, default=32, help='Independent Bell preparations per displayed pair')
    parser.add_argument('--seed', type=int, default=20261106)
    parser.add_argument('--step', action='store_true', help='Press Enter between stages')
    parser.add_argument('--delay', type=float, default=0, help='Automatic delay per stage, seconds (0..5)')
    parser.add_argument('--json', type=Path, help='Save the observer trace as JSON')
    args = parser.parse_args(argv)
    if args.seed < 0 or not 0 <= args.noise <= 1 or not 1 <= args.shots <= 1000 or not 1 <= args.pairs <= 32 or args.start < 0 or not 0 <= args.delay <= 5:
        parser.error('Invalid seed, probability, shots, pair count, start, or delay')
    print('SUPERDENSE QUANTUM VIEWER — OBSERVER MODE')
    print('Replay terpisah, bukan live tap server. State global hanya untuk observer simulator; tidak dikirim ke decoder chat.')
    print('Qubit order A,B; P(0)/P(1) lokal tidak memperlihatkan pilihan encoding ketika kedua qubit masih terpisah.')
    traces, frame_result = [], None
    if args.all_symbols:
        selected = [(index, bits) for index, bits in enumerate(LABELS)]
    elif args.bits:
        selected = [(0, args.bits)]
    else:
        if args.message is None:
            args.message = input('Pesan untuk dilihat (Enter = Hai!): ') if sys.stdin.isatty() else 'Hai!'
            if not args.message:
                args.message = 'Hai!'
        try:
            frame = encode_message(args.message, 1)
        except (ValueError, UnicodeError) as error:
            parser.error(str(error))
        payload = args.message.encode('utf-8')
        data = payload if args.scope == 'payload' else frame
        if data and args.start >= len(data) * 4:
            parser.error('--start is beyond the selected data')
        print(f'Pesan UTF-8: {args.message!r}\nPayload={len(payload)} byte; frame={len(frame)} byte (header={HEADER.size}, checksum=32).')
        print(f'Scope trace={args.scope}; total={len(data) * 4} pasangan. Trace dibatasi agar output terbaca.')
        pairs = [(index, f'{(byte >> shift) & 3:02b}') for index, (byte, shift) in
                 enumerate((byte, shift) for byte in data for shift in (6, 4, 2, 0))]
        selected = pairs[args.start:args.start + args.pairs]
        measured_frame = QuantumChannel(args.seed, args.noise).transmit(frame)
        try:
            received = decode_message(measured_frame)
            frame_result = {'accepted': True, 'received_text': received.text}
        except InvalidFrame as error:
            frame_result = {'accepted': False, 'received_text': None, 'error': str(error)}
        print('Verifikasi frame penuh (run terpisah):', json.dumps(frame_result, ensure_ascii=True))
        if not selected:
            print('Payload kosong: gunakan --scope frame untuk menelusuri header/checksum.')
    seeds = np.random.SeedSequence(args.seed).spawn(len(selected))
    try:
        for (index, bits), child in zip(selected, seeds):
            print(f'\n{"=" * 64}\nPAIR #{index} | input phase,flip = {bits} | noise={args.noise:g}')
            trace = trace_pair(bits, args.noise, int(child.generate_state(1)[0]), args.shots)
            trace['pair_index'] = index
            traces.append(trace)
            for number, record in enumerate(trace['stages'], 1):
                show_record(record, number, len(trace['stages']))
                if number < len(trace['stages']):
                    if args.step:
                        input('Enter untuk tahap berikutnya; Ctrl+C untuk berhenti...')
                    elif args.delay:
                        time.sleep(args.delay)
            print(f'Shot pertama: {trace["first_measurement"]}; cocok input={trace["first_measurement"] == bits}')
            print(f'Histogram {args.shots} persiapan Bell baru:', json.dumps(trace['histogram']))
    except (KeyboardInterrupt, EOFError):
        print('\nViewer dihentikan.')
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({'observer_only': True, 'live_server_tap': False,
            'seed': args.seed, 'frame_verification_separate_run': frame_result, 'traces': traces}, indent=2) + '\n')
        print('Trace tersimpan:', args.json)


if __name__ == '__main__':
    main()
