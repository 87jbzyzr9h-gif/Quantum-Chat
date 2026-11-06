# Superdense Chat

Chat terminal dua arah Bumi–Mars dengan engine Cirq + qsimcirq yang dibangun
ulang. Tidak ada QML, corpus latihan, tebakan pesan, pre-shared key, atau
fallback payload klasik dalam model pengiriman. Pasangan Bell yang dibagikan
adalah sumber daya quantum; itu berbeda dari pre-shared key kriptografi.

Ini **simulasi lokal**. Mac tidak mengirim qubit fisik. Dalam mode jaringan,
TCP localhost membawa perintah dan hasil simulator secara **klasik**, termasuk
teks yang dikirim pengguna ke backend tepercaya dan hasilnya ke terminal.
Tidak ada klaim bahwa TCP telah diubah menjadi quantum channel.

## Coba langsung dalam satu terminal

```sh
cd ~/Quantum-Lab
source .venv/bin/activate
python chat.py
```

Contoh percakapan:

```text
Bumi> Halo Mars 🚀
[Bumi → Mars #1, checksum OK] Halo Mars 🚀
[CONFIRMED #1] attempts=1
Bumi> /as Mars
Mars> Halo Bumi, diterima!
Mars> /history
Mars> /stats
Mars> /quit
```

`--demo` memilih mode yang sama secara eksplisit. Pengujian satu pesan:

```sh
python chat.py --message 'Hai! Apa kabarmu hari ini'
```

## Dua terminal peserta dan satu server simulator

Jalankan tiap perintah berikut dari `~/Quantum-Lab` memakai `.venv`.

Terminal server:

```sh
python chat.py --server
```

Terminal Bumi:

```sh
python chat.py --name Bumi
```

Terminal Mars:

```sh
python chat.py --name Mars
```

Setelah kedua peserta tersambung, ketik pesan biasa di salah satu terminal.
Penerima melihat teks yang telah melewati engine dan lolos checksum.
Server hanya bind ke `127.0.0.1`. Port default 8765; gunakan `--port 9000`
pada server dan kedua client jika port sedang dipakai. Satu nama hanya dapat
dipakai satu client aktif. Reconnect diperbolehkan setelah koneksi lama lepas.

## Perintah chat

| Perintah | Fungsi |
|---|---|
| Teks biasa | Kirim ke peserta lainnya |
| Baris kosong | Kirim pesan kosong |
| `/as Bumi` atau `/as Mars` | Ganti pengirim, khusus demo satu terminal |
| `/history` | Tampilkan sampai 100 pesan terakhir yang benar-benar diterima |
| `/stats` | Biaya model quantum dan biaya TCP simulator yang terpisah |
| `/send TEKS` | Kirim teks yang diawali `/`; `/send /quit` mengirim literal `/quit` |
| `/help` | Bantuan singkat |
| `/quit` | Keluar dari terminal peserta/demo |

Batas pesan 4096 byte UTF-8. Unicode, emoji, kata baru, teks tanpa tanda baca,
NUL dan beberapa baris didukung oleh protokol. Input interaktif satu baris;
gunakan `--message` untuk pengujian teks beberapa baris dari shell.
Karakter kontrol ditampilkan dalam bentuk escape agar tidak menjalankan
escape terminal. Byte pesan yang didecode tetap dipertahankan persis.

Riwayat bersifat sementara selama server/demo hidup, tidak ditulis ke disk
secara default. `--server --log logs/chat.jsonl` mengaktifkan log yang
**memuat isi percakapan**, hasil delivery, events dan resource. Tidak ada
autentikasi atau enkripsi; server ini dibatasi untuk eksperimen lokal.

## Alur superdense coding

1. Pesan menjadi frame: header 15 byte, teks UTF-8, checksum SHA-256 32 byte.
   Header mengirim versi, sequence dan panjang teks. Tidak ada target length
   tersembunyi atau lookup jawaban.
2. Setiap dua bit frame menggunakan satu Bell pair baru: H(A), CNOT(A,B).
   B diasumsikan sudah didistribusikan ke penerima dan biayanya dihitung.
3. Pengirim melakukan Z untuk phase bit dan X untuk flip bit pada A.
4. A berpindah ke penerima melalui tahap transfer yang eksplisit dalam model.
5. Penerima menjalankan CNOT(A,B), H(A), lalu mengukur A/B untuk mendapatkan
   dua bit. Engine hanya mengembalikan hasil pengukuran, tanpa state-vector.
6. Frame dibangun ulang dari pengukuran tersebut. Endpoint penerima hanya
   menerima frame hasil pengukuran; validasi checksum/header/UTF-8 dilakukan
   sebelum pesan masuk riwayat atau ditampilkan.
7. ACK/NACK 75 byte melalui saluran klasik model. ACK mengikat sequence dan
   fingerprint frame. Sender hanya berhenti retry setelah ACK valid cocok.

Referensi primer:
[IBM superdense coding](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/entanglement-in-action/superdense-coding).

Satu `run(repetitions=1)` per pasangan menghindari artefak pengurutan sampel
terminal multi-shot yang ditemukan pada eksperimen lama. Cache hanya berisi
circuit, bukan state atau jawaban; setiap shot mempersiapkan pasangan baru.

## Status dan gangguan

`CONFIRMED`: ACK valid kembali ke pengirim. `UNCONFIRMED`: batas attempts
habis tanpa ACK valid; penerima mungkin sudah menerima pesan. Jika ACK
hilang, frame yang dikirim ulang tidak ditambahkan sebagai pesan duplikat.
Sequence yang dipakai untuk isi berbeda ditolak. State duplikasi berlaku
dalam satu sesi, maksimum 10.000 sequence diterima per endpoint.

```sh
python chat.py --demo --noise 0.002 --ack-noise 0.0002 --attempts 5
```

`--noise`: probabilitas depolarisasi qubit A saat transit; I dengan peluang
1-p, X/Y/Z masing-masing p/3. `--ack-noise`: probabilitas flip tiap bit ACK
klasik. `--attempts` menghitung seluruh pengiriman termasuk percobaan pertama
(default 3, maksimum 20). Dalam mode dua terminal, opsi ini diatur pada
server. Bell preparation, distribusi B, penyimpanan dan gate lokal ideal;
tidak ada FEC, erasure, latensi jaringan fisik, atau hardware nyata.

Checksum mendeteksi kerusakan tak sengaja; SHA-256 tanpa kunci bukan
autentikasi. Keberhasilan tidak dijamin jika saluran terus rusak. Teks
yang rusak tidak diganti dengan tebakan bahasa.

## Dua jenis biaya yang berbeda

Biaya model superdense per attempt:

- `frame_bits`: jumlah bit header+payload+checksum yang dikodekan.
- `bell_pairs`, `sent_a_qubits`: masing-masing setengah `frame_bits`.
- `distributed_b_qubits`: satu distribusi B per pasangan baru.
- `classical_ack_bits`: semua ACK/NACK, termasuk yang rusak.
- `total_quantum_transfers`: distribusi B + pengiriman A; seluruh retry dihitung.
- `model_forward_classical_bits=0`: hanya berlaku di **model** payload maju.

Untuk target 25 byte, frame baru berukuran 72 byte = 576 bit, sehingga
memerlukan 288 Bell pair, 288 pengiriman A, 288 distribusi awal B, dan
600 bit ACK pada pengiriman ideal. Tidak ada kompresi tersembunyi.

Biaya runtime nyata dua terminal dicatat terpisah sebagai
`simulator_control_received_bytes` dan `simulator_control_sent_bytes`:
seluruh baris JSON/TCP untuk join, pesan, hasil, status, dan sistem yang
diproses server. Statistik merupakan snapshot sebelum balasan statistik
itu sendiri dikirim. Byte TCP tersebut bukan transfer qubit dan tidak
dimasukkan sebagai keuntungan quantum. Proses demo tunggal tidak memakai TCP.

## Struktur baru

```text
chat.py                  entry point
densechat/quantum.py      persiapan, transfer A, joint decoding qsimcirq
densechat/protocol.py     frame UTF-8, SHA-256, ACK
densechat/session.py      endpoint, riwayat, retry, resource ledger
densechat/server.py       kontrol simulator lewat localhost TCP
densechat/cli.py          demo dan terminal peserta
tests/                   tes protokol, quantum, percakapan, socket/CLI
verify_chat.py           200 acceptance trials dua arah
archives/                source, data, dan hasil lama yang diarsipkan
results/                 bukti verifikasi versi baru
```

Kode aktif baru tidak mengimpor source lama dan tidak memuat corpus, QML,
pre-shared key atau mode payload klasik. Environment `.venv` digunakan ulang;
dependensi aktif hanya Cirq, qsimcirq, NumPy. Paket lama di environment tidak
diuninstall karena tidak perlu untuk membangun ulang source aplikasi.

## Tes

```sh
python -m unittest discover -s tests -v
python verify_chat.py
```

Tes jaringan benar-benar membuka socket localhost sementara, bukan mock
transport. Pengujian acceptance menjalankan 100 pesan dua arah dalam kondisi
ideal dan 100 dalam kondisi berisik, termasuk pesan kosong dan Unicode.
CSV dan metadata disimpan ke `results/`. Angka keberhasilan berasal dari run,
bukan ditentukan di decoder. Lingkungan sandbox perlu izin bind localhost
untuk tes jaringan; Terminal macOS biasa tidak memakai sandbox Codex tersebut.


## Viewer proses quantum

```sh
python viewer.py --bits 11 --step
python viewer.py --message 'Hai!' --pairs 4 --step
python viewer.py --all-symbols --shots 32
python viewer.py --bits 11 --noise 0.1 --shots 100
python viewer.py --message 'Hai!' --scope frame --pairs 1 --json results/viewer-trace.json
```

Tanpa argumen, viewer meminta pesan di terminal interaktif; pada input
non-interaktif memakai demo `Hai!`. `--delay 0.5` menjalankan tampilan otomatis
setiap setengah detik. `--step` menunggu Enter antara tahap. Ctrl+C berhenti.
`--start` memilih indeks pasangan, `--pairs` membatasi jumlah pasangan yang
terlihat. Scope default hanya byte payload; scope `frame` mencakup header dan
checksum sebagaimana protokol chat.

Viewer memperlihatkan reset, H, CNOT/Bell pair, distribusi B, encoding Z/X,
transfer A, joint decoding dan pengukuran. Setiap tahap menampilkan circuit,
amplitudo ideal (qsimcirq), density matrix, probabilitas empat outcome, serta
marginal/Bloch vector/purity lokal A dan B. Noise memakai density matrix
ensemble eksak Cirq; tidak menampilkan satu trajectory sebagai state murni
keseluruhan. Histogram berasal dari shot qsimcirq independen, satu run per
pasangan Bell baru. State setelah pengukuran memperlihatkan hasil shot pertama.

Ini **observer replay terpisah**, belum live tap server chat. Global state hanya
untuk observer simulator, tidak pernah diberikan ke decoder chat. Verifikasi
frame penuh pada mode pesan adalah run terpisah dari trace pasangan yang
ditampilkan; hasil noisy kedua run tidak harus sama. Distribusi B dan transfer
A mengubah label kepemilikan; bukan gate yang otomatis mengubah state ideal.
Tanda minus global pada ket tidak mengubah probabilitas hasil pengukuran.
Viewer tidak memakai history chat, QML, corpus, atau pre-shared key baru.
