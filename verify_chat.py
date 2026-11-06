"""Run reproducible two-way acceptance trials on the new chat engine."""
import argparse
import csv
import importlib.metadata
import json
from pathlib import Path
import sys

from densechat.session import ChatSession


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('results'))
    parser.add_argument('--seed', type=int, default=20261106)
    args = parser.parse_args()
    rows, summaries = [], []
    for profile, noise, ack_noise, attempts in [('ideal', 0.0, 0.0, 1), ('noisy', 0.002, 0.0002, 5)]:
        session = ChatSession(args.seed, noise, ack_noise, attempts)
        for name in ('Bumi', 'Mars'):
            session.add_endpoint(name)
        group = []
        for index in range(100):
            sender, recipient = ('Bumi', 'Mars') if index % 2 == 0 else ('Mars', 'Bumi')
            truth = 'Hai! Apa kabarmu hari ini' if index == 0 else f'Pesan baru #{index}: {sender} → {recipient} 🌏 nilai {index * 7919}'
            if index == 1:
                truth = ''
            elif index == 2:
                truth = '你好\nمرحبا\0🚀'
            result = session.send(sender, recipient, truth)
            row = {'profile': profile, 'trial': index + 1, 'sender': sender, 'recipient': recipient,
                   'exact_received': result.received and result.received_text == truth,
                   'wrong_received': result.received and result.received_text != truth,
                   'confirmed': result.confirmed, 'received': result.received, 'attempts': result.attempts,
                   'truth': truth, 'receiver_text': result.received_text, **result.resources}
            rows.append(row)
            group.append(row)
        summary = {'profile': profile, 'trials': 100, 'exact_received': sum(r['exact_received'] for r in group),
                   'confirmed': sum(r['confirmed'] for r in group), 'wrong_received': sum(r['wrong_received'] for r in group),
                   'noise': noise, 'ack_noise': ack_noise, 'attempt_limit': attempts, 'resources': session.totals.to_dict()}
        summaries.append(summary)
        print(json.dumps(summary), flush=True)
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output/'trials.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (args.output/'verification.json').write_text(json.dumps({'seed': args.seed, 'python': sys.version,
        'packages': {p: importlib.metadata.version(p) for p in ['cirq-core', 'qsimcirq', 'numpy']},
        'profiles': summaries, 'scope': 'Local engine acceptance trials; socket integration is covered by unit tests'}, indent=2)+'\n')


if __name__ == '__main__':
    main()
