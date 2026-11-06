"""Demo satu terminal atau chat dua terminal, tanpa dependensi UI opsional. / One-terminal demo or two-terminal chat, with no optional UI dependencies."""
import argparse
import json
from pathlib import Path
import queue
import socket
import threading

from .server import MAX_LINE_BYTES, MAX_RESPONSE_BYTES, NAMES, SimulatorServer, wire_json
from .session import ChatSession


NOTICE = 'SUPERDENSE CHAT — SIMULASI LOKAL / LOCAL SIMULATION\nQubit A dipindahkan dalam model sebelum decoding bersama. / Qubit A is transferred in the model before joint decoding. TCP lokal = kontrol klasik simulator. / Local TCP = classical simulator control.'


def visible(text: str) -> str:
    escapes = {'\n': '\\n', '\r': '\\r', '\t': '\\t'}
    return ''.join(escapes.get(char, f'\\x{ord(char):02x}') if ord(char) < 32 or ord(char) == 127 else char for char in text)


def print_resources(resources: dict):
    print(f'  Pasangan Bell / Bell pairs: {resources["bell_pairs"]} | A dikirim / A sent: {resources["sent_a_qubits"]} | '
          f'B didistribusikan / B distributed: {resources["distributed_b_qubits"]} | ACK klasik / Classical ACK: {resources["classical_ack_bits"]} bit', flush=True)


def display(event: dict):
    kind = event.get('kind')
    if kind == 'message':
        print(f'\n[{event["sender"]} → {event["recipient"]} #{event["sequence"]}, checksum OK] {visible(event["text"])}', flush=True)
    elif kind in ('system', 'error'):
        print(f'\n[{kind}] {visible(event["text"])}', flush=True)
    elif kind == 'receipt':
        print(f'[{event["status"]} #{event["sequence"]}] percobaan / attempts={event["attempts"]}', flush=True)
        print_resources(event['resources'])
        if event['status'] == 'UNCONFIRMED':
            print('  ACK belum valid setelah batas percobaan; penerima mungkin sudah menerima pesan. / No valid ACK within the attempt limit; the recipient may already have the message.', flush=True)
    elif kind == 'history':
        if not event['messages']:
            print('(Riwayat masih kosong / History is empty)', flush=True)
        for message in event['messages']:
            print(f'#{message["sequence"]} {message["sender"]} → {message["recipient"]}: {visible(message["text"])}', flush=True)
    elif kind == 'stats':
        print(json.dumps(event['data'], indent=2, ensure_ascii=True), flush=True)


def demo(args):
    session = ChatSession(args.seed, args.noise, args.ack_noise, args.attempts)
    for name in NAMES:
        session.add_endpoint(name)
    sender = 'Bumi'
    print(NOTICE + '\nDemo dua arah / Two-way demo: /as Bumi, /as Mars, /history, /stats, /help, /quit', flush=True)
    while True:
        try:
            text = args.message if args.message is not None else input(f'{sender}> ')
        except (EOFError, KeyboardInterrupt):
            print('\nSesi selesai. / Session ended.')
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
                        print('Pilih Bumi atau Mars. / Choose Bumi or Mars.')
                elif text == '/history':
                    display({'kind': 'history', 'messages': session.history[-100:]})
                elif text == '/stats':
                    display({'kind': 'stats', 'data': session.stats()})
                elif text == '/help':
                    print('Teks biasa mengirim pesan; /send TEKS untuk teks berawalan slash. / Plain text sends a message; /send TEXT sends slash-prefixed text. /as Bumi|Mars, /history, /stats, /quit.')
                else:
                    print('Perintah tidak dikenal; gunakan /help. / Unknown command; use /help.')
                continue
        other = next(name for name in NAMES if name != sender)
        try:
            result = session.send(sender, other, text)
        except (ValueError, UnicodeError) as error:
            print('Tidak dapat mengirim / Cannot send:', error)
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
            raise RuntimeError('Server menutup koneksi saat masuk / Server closed the connection during login')
        welcome = json.loads(line)
        if welcome.get('kind') != 'welcome':
            raise RuntimeError(welcome.get('text', 'Server menolak koneksi / Server refused the connection'))
        print('Tersambung sebagai / Connected as', args.name, '| /history, /stats, /help, /quit', flush=True)
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
                    print('Teks biasa mengirim pesan; /send TEKS untuk teks berawalan slash. / Plain text sends a message; /send TEXT sends slash-prefixed text. /history, /stats, /quit.')
                    continue
                if text in ('/history', '/stats'):
                    request = {'action': text[1:]}
                elif text == '/send' or text.startswith('/send '):
                    request = {'action': 'send', 'text': text[6:] if text.startswith('/send ') else ''}
                elif text.startswith('/'):
                    print('Perintah tidak dikenal; gunakan /help. / Unknown command; use /help.')
                    continue
                else:
                    request = {'action': 'send', 'text': text}
                connection.sendall(wire_json(request))
                response = responses.get(timeout=60)
                if response.get('kind') == 'closed':
                    print('Server terputus. / Server disconnected.')
                    return
                display(response)
        except (EOFError, KeyboardInterrupt):
            print('\nSesi selesai. / Session ended.')
        finally:
            try:
                connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            thread.join(timeout=1)
            reader.close()


def main(argv=None):
    parser = argparse.ArgumentParser(add_help=False, description='Chat terminal superdense, simulasi quantum lokal / Superdense terminal chat, local quantum simulation')
    parser.add_argument('-h', '--help', action='help', help='Tampilkan bantuan lalu keluar / Show this help and exit')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--server', action='store_true', help='Jalankan server lokal / Run the local server')
    mode.add_argument('--name', choices=NAMES, help='Hubungkan terminal ke server simulator / Connect a terminal to the simulator server')
    mode.add_argument('--demo', action='store_true', help='Simulasi dua arah satu terminal (bawaan) / One-terminal two-way simulation (default)')
    parser.add_argument('--message', help='Kirim satu pesan dalam demo lalu keluar / Send one message in demo mode and exit')
    parser.add_argument('--port', type=int, default=8765, help='Port TCP localhost / Localhost TCP port')
    parser.add_argument('--seed', type=int, default=20261106, help='Seed acak nonnegatif / Nonnegative random seed')
    parser.add_argument('--noise', type=float, default=0, help='Peluang depolarisasi per A terkirim / Depolarization probability per transmitted A')
    parser.add_argument('--ack-noise', type=float, default=0, help='Peluang bit ACK klasik terbalik / Classical ACK bit-flip probability')
    parser.add_argument('--attempts', type=int, default=3, help='Batas percobaan (1..20) / Attempt limit (1..20)')
    parser.add_argument('--log', type=Path, help='Simpan log pengiriman JSONL bila dipilih (berisi teks chat) / Opt-in server JSONL delivery log (contains chat text)')
    args = parser.parse_args(argv)
    if args.seed < 0 or not 0 <= args.noise <= 1 or not 0 <= args.ack_noise <= 1 or not 1 <= args.attempts <= 20 or not 0 <= args.port <= 65535:
        parser.error('Seed, peluang, port, atau batas percobaan tidak valid / Invalid seed, probability, port, or attempt limit')
    if args.message is not None and (args.server or args.name):
        parser.error('--message hanya untuk demo; ketik di klien tersambung / --message is for demo mode; type messages in a connected client')
    if args.log and not args.server:
        parser.error('--log memerlukan --server / --log requires --server')
    try:
        if args.server:
            with SimulatorServer(args.port, seed=args.seed, noise=args.noise, ack_noise=args.ack_noise,
                                 attempts=args.attempts, log=args.log) as server:
                print(NOTICE + f'\nServer: 127.0.0.1:{server.server_address[1]} (Ctrl+C untuk berhenti / Ctrl+C to stop)', flush=True)
                server.serve_forever(poll_interval=0.1)
        elif args.name:
            client(args)
        else:
            demo(args)
    except (OSError, RuntimeError, queue.Empty) as error:
        print(f'Tidak dapat melanjutkan / Cannot continue: {error}')
        raise SystemExit(1)
    except KeyboardInterrupt:
        print('\nServer berhenti. / Server stopped.')


if __name__ == '__main__':
    main()
