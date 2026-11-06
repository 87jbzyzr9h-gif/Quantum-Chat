# Quantum Chat — Bahasa Indonesia

Versi **0.1.0 research preview**, lisensi MIT. Simulator lokal superdense coding
dengan chat dua arah, viewer observer dan notebook ilmiah yang bisa dieksekusi.
Tidak ada klaim pengiriman qubit fisik melalui TCP atau komunikasi instan.

## Instalasi

```sh
git clone https://github.com/87jbzyzr9h-gif/Quantum-Chat.git
cd Quantum-Chat
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --only-binary=:all: -r requirements.txt
python -m pip install --no-deps .
python chat.py
```

Ketik pesan, `/as Mars` untuk membalas sebagai Mars, `/history` untuk riwayat,
`/stats` untuk statistik, dan `/quit` untuk keluar. Untuk dua peserta,
jalankan `python chat.py --server`, lalu `python chat.py --name Bumi` dan
`python chat.py --name Mars` pada dua terminal lain di folder/env yang sama.

TCP localhost mengirim teks/perintah ke backend simulator dan hasilnya ke
terminal secara klasik. Biaya model quantum dicatat terpisah. Server hanya
localhost dan tidak memiliki autentikasi/enkripsi. Logging isi chat opt-in.

## Notebook ilmiah

```sh
python -m pip install -e '.[notebooks,dev]'
jupyter lab
```

1. [Dasar superdense coding](notebooks/01_superdense_coding.ipynb): persamaan,
   circuit, Bell state, marginal B, empat simbol dan pengukuran nyata qsim.
2. [Arsitektur dan protokol](notebooks/02_quantum_chat_protocol.ipynb): diagram,
   UTF-8, frame/ACK, dua arah, biaya, noise dan interval statistik.
3. [Observer dan noise](notebooks/03_observer_and_noise.ipynb): amplitudo/fase,
   density matrix, state campuran dan histogram shot.

Notebook berisi keluaran eksekusi dan assertion, tanpa data unduhan atau
jawaban tersembunyi. State global hanya di observer. Tidak ada QML, corpus,
pre-shared-key reconstruction atau pengiriman data lewat entanglement saja.

## Viewer dan verifikasi

```sh
python viewer.py --bits 11 --step
python viewer.py --bits 11 --noise 0.1 --shots 100
python -m unittest discover -s tests -v
python verify_chat.py
python scripts/execute_notebooks.py --output work/executed-notebooks
```

Viewer adalah replay terpisah, belum live tap server. Pesan contoh 25 byte
memerlukan frame 72 byte: 288 Bell pair, 288 transfer A, 288 distribusi B dan
600 bit ACK per attempt ideal. Tidak ada kompresi/informasi gratis tersembunyi.

Lihat [teori](docs/theory.md), [arsitektur](docs/architecture.md),
[reproduksibilitas](docs/reproducibility.md), [referensi](docs/references.bib),
dan [panduan lengkap](README.md).
