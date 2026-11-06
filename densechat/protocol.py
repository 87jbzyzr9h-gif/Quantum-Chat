"""Frame data UTF-8 dan ACK klasik dengan checksum SHA-256. / UTF-8 data frames and classical acknowledgements with SHA-256 checksums."""
from dataclasses import dataclass
import hashlib
import hmac
import struct

HEADER = struct.Struct('!2sBQI')  # magic, version, sequence, UTF-8 byte length
ACK = struct.Struct('!2sBQ32s')  # magic, accepted, sequence, exact frame fingerprint
DIGEST_SIZE = 32
ACK_SIZE = ACK.size + DIGEST_SIZE
MAX_TEXT_BYTES = 4096


class InvalidFrame(ValueError):
    pass


def digest(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def checked_body(wire: bytes) -> bytes:
    if len(wire) < DIGEST_SIZE or not hmac.compare_digest(digest(wire[:-DIGEST_SIZE]), wire[-DIGEST_SIZE:]):
        raise InvalidFrame('Checksum tidak cocok / Checksum mismatch')
    return wire[:-DIGEST_SIZE]


def encode_message(text: str, sequence: int) -> bytes:
    raw = text.encode('utf-8')
    if len(raw) > MAX_TEXT_BYTES:
        raise ValueError(f'Pesan maksimum {MAX_TEXT_BYTES} byte UTF-8 / Message limit: {MAX_TEXT_BYTES} UTF-8 bytes')
    if not 1 <= sequence < 2 ** 64:
        raise ValueError('Sequence di luar rentang protokol / Sequence outside protocol range')
    body = HEADER.pack(b'SD', 1, sequence, len(raw)) + raw
    return body + digest(body)


@dataclass(frozen=True, slots=True)
class Received:
    text: str
    sequence: int
    fingerprint: bytes


def decode_message(wire: bytes) -> Received:
    if not HEADER.size + DIGEST_SIZE <= len(wire) <= HEADER.size + MAX_TEXT_BYTES + DIGEST_SIZE:
        raise InvalidFrame('Panjang frame di luar batas / Frame length outside bounds')
    body = checked_body(wire)
    magic, version, sequence, length = HEADER.unpack(body[:HEADER.size])
    if magic != b'SD' or version != 1 or not sequence or length != len(body) - HEADER.size:
        raise InvalidFrame('Header frame tidak valid / Invalid frame header')
    try:
        text = body[HEADER.size:].decode('utf-8')
    except UnicodeDecodeError as error:
        raise InvalidFrame('Payload UTF-8 tidak valid / Invalid UTF-8 payload') from error
    return Received(text, sequence, digest(wire))


def encode_ack(sequence: int = 0, fingerprint: bytes = b'\0' * 32, accepted: bool = False) -> bytes:
    body = ACK.pack(b'SA', int(accepted), sequence, fingerprint)
    return body + digest(body)


def valid_ack(wire: bytes, sequence: int, fingerprint: bytes) -> bool:
    if len(wire) != ACK_SIZE:
        return False
    try:
        magic, accepted, received_sequence, received_digest = ACK.unpack(checked_body(wire))
    except InvalidFrame:
        return False
    return magic == b'SA' and accepted == 1 and received_sequence == sequence and received_digest == fingerprint
