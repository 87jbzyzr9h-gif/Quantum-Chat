"""One-terminal demo or two-terminal chat, with no optional UI dependencies."""
import argparse
import json
from pathlib import Path
import queue
import socket
import threading

from .server import MAX_LINE_BYTES, MAX_RESPONSE_BYTES, NAMES, SimulatorServer, wire_json
from .session import ChatSession


NOTICE = 'SUPERDENSE CHAT — SIMULASI LOKAL\nQubit A dipindahkan dalam model sebelum joint decoding. TCP lokal = kontrol klasik simulator.'


def visible(text: str) -> str:
    escapes = {'\n': '\\n', '\r': '\\r', '\t': '\\t'}
    return ''.join(escapes.get(char, f'\\x{ord(char):02x}') if ord(char) < 32 or ord(char) == 127 else char for char in text)


def print_resources(resources: dict):
    print(f'  Bell pair: {resources["bell_pairs"]} | A dikirim: {resources["sent_a_qubits"]} | '
          f'B didistribusikan: {resources["distributed_b_qubits"]} | ACK klasik: {resources["classical_ack_bits"]} bit', flush=True)


def display(event: dict):
    kind = event.get('kind')
    if kind == 'message':
        print(f'\n[{event["sender"]} → {event["recipient"]} #{event["sequence"]}, checksum OK] {visible(event["text"])}', flush=True)
    elif kind in ('system', 'error'):
        print(f'\n[{kind}] {visible(event["text"])}', flush=True)
    elif kind == 'receipt':
        print(f'[{event["status"]} #{event["sequence"]}] attempts={event["attempts"]}', flush=True)
        print_resources(event['resources'])
        if event['status'] == 'UNCONFIRMED':
            print('  ACK belum valid setelah batas attempts; penerima mungkin sudah menerima pesan.', flush=True)
    elif kind == 'history':
        if not event['messages']:
            print('(Riwayat masih kosong)', flush=True)
        for message in event['messages']:
            print(f'#{message["sequence"]} {message["sender"]} → {message["recipient"]}: {visible(message["text"])}', flush=True)
    elif kind == 'stats':
        print(json.dumps(event['data'], indent=2, ensure_ascii=True), flush=True)


def demo(args):
    session = ChatSession(args.seed, args.noise, args.ack_noise, args.attempts)
    for name in NAMES:
        session.add_endpoint(name)
    sender = 'Bumi'
    print(NOTICE + '\nDemo dua arah: /as Bumi, /as Mars, /history, /stats, /help, /quit', flush=True)
    while True:
        try:
            text = args.message if args.message is not None else input(f'{sender}> ')
        except (EOFError, KeyboardInterrupt):
            print('\nSesi selesai.')
            return
        if args.message is None and text.startswith('/'):
            if text == '/send' or text.startswith('/send '):
                text = text[6:] if text.startswith('/send ') else ''
            else:
                if text == '/quit':
                    return
                if text.startswith('/as '):
                    name = text[4:].strip().capitalize()
                    if name in NAMES:
                        sender = name
                    else:
                        print('Pilih Bumi atau Mars.')
                elif text == '/history':
                    display({'kind': 'history', 'messages': session.history[-100:]})
                elif text == '/stats':
                    display({'kind': 'stats', 'data': session.stats()})
                elif text == '/help':
                    print('Teks biasa mengirim pesan. /as Bumi|Mars, /history, /stats, /quit. /send TEKS mengirim teks berawalan slash.')
                else:
                    print('Perintah tidak dikenal; gunakan /help.')
                continue
        other = next(name for name in NAMES if name != sender)
        try:
            result = session.send(sender, other, text)
        except (ValueError, UnicodeError) as error:
            print('Tidak dapat mengirim:', error)
            if args.message is not None:
                raise SystemExit(2)
            continue
        if result.received:
            display({'kind': 'message', 'sender': sender, 'recipient': other,
                     'sequence': result.sequence, 'text': result.received_text})
        display({'kind': 'receipt', 'sequence': result.sequence, 'status': result.status,
                 'attempts': result.attempts, 'resources': result.resources})
        if args.message is not None:
            return


def client(args):
    print(NOTICE, flush=True)
    with socket.create_connection(('127.0.0.1', args.port), timeout=5) as connection:
        connection.settimeout(None)
        reader = connection.makefile('rb')
        connection.sendall(wire_json({'action': 'join', 'name': args.name}))
        line = reader.readline(MAX_LINE_BYTES + 1)
        if not line:
            raise RuntimeError('Server menutup koneksi saat login')
        welcome = json.loads(line)
        if welcome.get('kind') != 'welcome':
            raise RuntimeError(welcome.get('text', 'Server menolak koneksi'))
        print('Tersambung sebagai', args.name, '| /history, /stats, /help, /quit', flush=True)
        responses = queue.Queue()

        def receive():
            try:
                while True:
                    data = reader.readline(MAX_RESPONSE_BYTES + 1)
                    if not data or len(data) > MAX_RESPONSE_BYTES:
                        break
                    event = json.loads(data)
                    if event.get('kind') in ('message', 'system'):
                        display(event)
                    else:
                        responses.put(event)
            except (OSError, ValueError):
                pass
            finally:
                responses.put({'kind': 'closed'})

        thread = threading.Thread(target=receive, daemon=True)
        thread.start()
        try:
            while True:
                text = input(f'{args.name}> ')
                if text == '/quit':
                    connection.sendall(wire_json({'action': 'quit'}))
                    return
                if text == '/help':
                    print('Teks biasa mengirim pesan. /history, /stats, /quit, /send TEKS untuk teks berawalan slash.')
                    continue
                if text in ('/history', '/stats'):
                    request = {'action': text[1:]}
                elif text == '/send' or text.startswith('/send '):
                    request = {'action': 'send', 'text': text[6:] if text.startswith('/send ') else ''}
                elif text.startswith('/'):
                    print('Perintah tidak dikenal; gunakan /help.')
                    continue
                else:
                    request = {'action': 'send', 'text': text}
                connection.sendall(wire_json(request))
                response = responses.get(timeout=60)
                if response.get('kind') == 'closed':
                    print('Server terputus.')
                    return
                display(response)
        except (EOFError, KeyboardInterrupt):
            print('\nSesi selesai.')
        finally:
            try:
                connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            thread.join(timeout=1)
            reader.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description='Superdense terminal chat, local quantum simulation')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--server', action='store_true')
    mode.add_argument('--name', choices=NAMES, help='Connect a terminal to the simulator server')
    mode.add_argument('--demo', action='store_true', help='One-terminal two-way simulation (default)')
    parser.add_argument('--message', help='Send one message in demo mode and exit')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--seed', type=int, default=20261106)
    parser.add_argument('--noise', type=float, default=0, help='Depolarization probability per transmitted A')
    parser.add_argument('--ack-noise', type=float, default=0, help='Classical ACK bit-flip probability')
    parser.add_argument('--attempts', type=int, default=3)
    parser.add_argument('--log', type=Path, help='Opt-in server JSONL delivery log (contains chat text)')
    args = parser.parse_args(argv)
    if args.seed < 0 or not 0 <= args.noise <= 1 or not 0 <= args.ack_noise <= 1 or not 1 <= args.attempts <= 20 or not 0 <= args.port <= 65535:
        parser.error('Seed, probability, port, or attempt limit is invalid')
    if args.message is not None and (args.server or args.name):
        parser.error('--message is for demo mode; type messages in a connected client')
    if args.log and not args.server:
        parser.error('--log requires --server')
    try:
        if args.server:
            with SimulatorServer(args.port, seed=args.seed, noise=args.noise, ack_noise=args.ack_noise,
                                 attempts=args.attempts, log=args.log) as server:
                print(NOTICE + f'\nServer: 127.0.0.1:{server.server_address[1]} (Ctrl+C untuk berhenti)', flush=True)
                server.serve_forever(poll_interval=0.1)
        elif args.name:
            client(args)
        else:
            demo(args)
    except (OSError, RuntimeError, queue.Empty) as error:
        print(f'Tidak dapat melanjutkan: {error}')
        raise SystemExit(1)
    except KeyboardInterrupt:
        print('\nServer berhenti.')


if __name__ == '__main__':
    main()
