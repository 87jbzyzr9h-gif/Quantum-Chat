# Reproduksibilitas

[English](reproducibility.md) | Bahasa Indonesia

Gunakan Python 3.12 dan versi runtime yang dikunci dalam `requirements.txt`.
Jupyter dan alat build tersedia sebagai tambahan opsional. Komputasi notebook
tidak memakai data pribadi, pelatihan model, API key, atau unduhan jaringan.

```sh
python -m unittest discover -s tests -v
python verify_chat.py --output work/acceptance
python scripts/execute_notebooks.py --output work/executed-notebooks
```

Skrip eksekusi menghapus keluaran kode, memulai kernel bersih per notebook,
menjalankan setiap sel kode, memvalidasi format, dan menolak keluaran error.
Gambar di `docs/figures/` dibuat ulang. `--in-place` memperbarui keluaran dalam
repository. Timestamp eksekusi sel dihapus untuk mengurangi diff yang tak relevan.

Sel setup notebook melaporkan versi, bukan path pribadi. Seed dan seluruh
parameter noise, pesan, dan pengulangan dinyatakan eksplisit. Backend/versi/
platform berbeda dapat menghasilkan urutan acak berbeda meski seed sama.

Periksa bahwa empat simbol ideal di-decode benar; semua state Bell terenkode
memiliki rho_B=I/2; teks UTF-8 diterima sama dengan yang dikirim; frame rusak
tidak menghasilkan pesan tebakan; setiap pengulangan memakai pasangan baru
dan menghitung biaya ACK. Bandingkan sampel berisik dengan ensemble dan
ketidakpastian sampel terbatas, serta pisahkan penerimaan dari konfirmasi.

Notebook 02 memakai pesan sintetik sebagai fixture transport. Tidak ada model
bahasa yang dilatih. Interval Wilson menjelaskan simulasi yang dipilih, bukan
kinerja hardware atau bukti no-signalling.

Distribusi source memuat docs/notebook/tes. Wheel berisi runtime dan modul
observer. Artefak rilis GitHub menyertakan checksum SHA-256. Tidak ada klaim
publikasi PyPI atau DOI software.

Mirror private menyalin branch/tag Git. Issue GitHub, log Actions, dan metadata
aset rilis bukan ref Git sehingga tidak disalin oleh `push --mirror`.
