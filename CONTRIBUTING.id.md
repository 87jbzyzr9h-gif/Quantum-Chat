# Berkontribusi

[English](CONTRIBUTING.md) | Bahasa Indonesia

Gunakan Python 3.12 dan buat virtual environment baru:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[notebooks,dev]'
python -m unittest discover -s tests -v
python scripts/execute_notebooks.py --output work/executed-notebooks
python -m build
```

Pisahkan sumber daya quantum simulasi dari kanal kontrol TCP klasik. Gunakan
satu shot qsimcirq per pasangan baru. Perubahan encoding, urutan byte, validasi
frame, atau perhitungan sumber daya memerlukan tes roundtrip/kegagalan yang
bermakna. Jangan berikan teks asli pengirim, pilihan encoding, atau state
global kepada endpoint penerima. Akses state global hanya untuk observer dan
tes fisika.

Keluaran notebook harus berasal dari eksekusi dengan seed tetap dan parameter
lengkap. Jangan hardcode jumlah keberhasilan atau melatih dengan pesan
evaluasi. Jelaskan keterbatasan dan kutip sumber primer. Notebook harus bisa
dijalankan dari awal sampai akhir tanpa unduhan jaringan, kredensial, path
pribadi absolut, atau state tersembunyi.

Perbarui pasangan dokumen English/Indonesia bersama. Setiap bagian naratif
notebook dan label diagram memiliki kedua bahasa. Pesan terminal memakai
kedua bahasa; identifier kode, perintah, status, dan field JSON tetap sama.
Judul karya ilmiah dan identifier bibliografi dipertahankan sesuai sumber.

Dalam laporan bug sertakan versi rilis, OS, versi Python/dependensi, perintah,
seed, dan pesan sintetik minimal. Jangan unggah log chat pribadi, kredensial,
atau informasi pribadi. Server pratinjau ini hanya localhost tanpa autentikasi/
enkripsi; jangan jadikan layanan publik.

Kontribusi mengikuti lisensi MIT repository.
