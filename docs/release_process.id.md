# Rilis public dan mirror private

[English](release_process.md) | Bahasa Indonesia

`Quantum-Chat` adalah repository public utama. `origin` memakai push branch/tag
biasa, bukan `push --mirror` dari checkout kerja. Repository terpisah
`Quantum-Chat-Private` merupakan mirror Git private atas riwayat branch/tag
public. Ini bukan kanal pesan chat private atau fitur kriptografi simulator.

Urutan rilis:

1. Tinjau source, keluaran notebook, dan riwayat Git untuk kredensial/data pribadi.
2. Jalankan tes unit/jaringan, uji penerimaan, semua notebook, dan build paket.
3. Push commit rilis secara biasa ke `main` public, lalu tunggu CI.
4. Buat tag versi dan rilis pratinjau riset GitHub berisi source, wheel/notebook, serta checksum SHA-256. Lisensi MIT dan metadata CFF menyertainya.
5. Sinkronkan mirror private khusus dan bandingkan ID objek seluruh branch/tag.

Helper mirror (memerlukan Git dan GitHub CLI terautentikasi):

```sh
python scripts/sync_private_mirror.py         # tinjau pratinjau dahulu
python scripts/sync_private_mirror.py --apply # mirror branch/tag
```

Helper memeriksa tujuan private, menolak sumber/tujuan identik, memakai
repository bare khusus, dan mengambil hanya branch/tag proyek. Ref editor/
Codex, virtualenv lokal, log chat, dan berkas work yang diabaikan tidak di-mirror.
Semantik mirror memperbarui atau menghapus ref tujuan agar sama dengan sumber.
Issue GitHub, log Actions, dan aset rilis bukan ref Git sehingga tidak ikut
direplikasi. Token tidak disimpan dalam repository.

Rilis public awal `v0.1.0` ditandai sebagai pratinjau riset. Tidak ada publikasi
PyPI, DOI software, koneksi hardware, atau klaim tinjauan sejawat.

Versi `v0.1.1` melengkapi dokumentasi dan tampilan Indonesia/English.
Tag historis dan aset rilis awal tetap sebagaimana diterbitkan.
