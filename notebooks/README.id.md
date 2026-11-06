# Notebook ilmiah

[English](README.md) | Bahasa Indonesia

Jalankan dengan Python 3.12 setelah `python -m pip install -e '.[notebooks,dev]'`.
Pilih kernel environment itu dan jalankan semua sel dari awal sampai akhir.
Narasi setiap notebook tersedia dalam Bahasa Indonesia dan English, dengan
persamaan/kode bersama serta label gambar dan keluaran penjelasan bilingual.

1. **01_superdense_coding.ipynb**: konvensi, persiapan Bell, circuit, verifikasi
   empat simbol qsim, partial trace, dan diagram fase/koherensi.
2. **02_quantum_chat_protocol.ipynb**: arsitektur, pengiriman frame dua arah
   aktual, overhead, kontrol ACK hilang, uji 100 pesan ideal/berisik, dan
   interval Wilson deskriptif.
3. **03_observer_and_noise.ipynb**: sepuluh tahap observer, fase versus populasi,
   ensemble campuran eksak, histogram sampling, dan kemurnian.

Setiap notebook menyertakan referensi primer, seed tetap, keluaran versi,
hasil eksekusi aktual, assertion, dan keterbatasan. Gambar juga diekspor
ke `docs/figures/` dalam format PNG/SVG. Eksekusi tidak memerlukan dataset
unduhan, kredensial, atau corpus pelatihan.

Inspeksi state global adalah hak diagnostik observer, bukan masukan penerima
chat. Kanal kontrol localhost adalah klasik. A harus ditransfer dalam model
sebelum decoding bersama; tidak ada transfer qubit fisik.

Eksekusi ulang tanpa mengganti keluaran tersimpan:

```sh
python scripts/execute_notebooks.py --output work/executed-notebooks
```

Gunakan `--in-place` hanya untuk sengaja memperbarui keluaran ilmiah. Baca
[teori](../docs/theory.id.md) dan [metodologi](../docs/reproducibility.id.md)
untuk asumsi dan cakupan hasil numerik.
