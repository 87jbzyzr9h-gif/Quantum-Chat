# Cakupan ilmiah dan persamaan

[English](theory.md) | Bahasa Indonesia

Ini implementasi superdense coding yang sudah dikenal untuk pendidikan dan
eksplorasi numerik yang dapat direproduksi, bukan hukum komunikasi baru.

## Konvensi

Urutan basis A,B: |00>, |01>, |10>, |11>. Siapkan

\[
|\Phi^+\rangle=\operatorname{CNOT}_{A\to B}(H_A\otimes I_B)|00\rangle
=(|00\rangle+|11\rangle)/\sqrt 2.
\]

Untuk bit z,x, terapkan Z^z lalu X^x, menghasilkan operator X^x Z^z pada A.
Setelah A tiba di penerima, CNOT lalu H(A) menghasilkan

\[
(H_A\otimes I_B)\operatorname{CNOT}_{A\to B}
(X_A^x Z_A^z\otimes I_B)|\Phi^+\rangle=e^{i\theta}|zx\rangle.
\]

Fase global tidak teramati. Empat state Bell ortogonal dibedakan bersama.
Setiap A terkirim mewakili dua bit klasik dengan satu pasangan Bell yang
sudah dibagikan; distribusinya merupakan sumber daya terpisah. Lihat
[Bennett & Wiesner (1992)](https://doi.org/10.1103/PhysRevLett.69.2881) dan
[protokol IBM](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/entanglement-in-action/superdense-coding).

## State marginal dan no-signalling

Untuk setiap state Bell terenkode,

\[
\rho_B=\operatorname{Tr}_A(|\psi_{zx}\rangle\langle\psi_{zx}|)=I/2.
\]

Maka P(B=0)=P(B=1)=1/2, tidak bergantung pada z,x. Penambahan sampel lokal
atau classifier tidak mengubah marginal ideal tersebut. A harus tiba agar
decoding bersama dapat dilakukan. Amplitudo observer tidak diberikan ke
penerima logis. [State tereduksi IBM](https://quantum.cloud.ibm.com/learning/en/courses/general-formulation-of-quantum-information/density-matrices/multiple-systems).

## Noise dan percobaan ulang

Kanal transit A dalam model adalah

\[
\mathcal E_p(\rho)=(1-p)\rho+\frac p3
(X_A\rho X_A+Y_A\rho Y_A+Z_A\rho Z_A).
\]

Decoder bersama menghasilkan simbol benar dengan peluang 1-p dan masing-masing
simbol lainnya p/3. Ensemble umumnya campuran; matriks densitas eksak
menjelaskannya, sedangkan eksekusi satu shot qsimcirq menyediakan histogram
pengukuran.

Untuk panjang frame L byte, m=4L simbol. Dengan asumsi error transit independen,
gate/persiapan ideal, dan peluang tabrakan checksum dapat diabaikan, peluang
frame utuh tanpa perubahan adalah (1-p)^m. ACK 75 byte bertahan dari error bit
independen q dengan peluang (1-q)^600. Maka pendekatan model konfirmasi untuk
R percobaan adalah

\[
s=(1-p)^{4L}(1-q)^{600},\qquad P(\text{confirmed by }R)=1-(1-s)^R.
\]

Persamaan tidak mencakup erasure, noise penyimpanan, distribusi Bell tidak
sempurna, error hardware, latensi fisik, atau lalu lintas adversarial. Pesan
dengan panjang bervariasi tidak boleh diwakili satu kurva benchmark L tetap.

## Batas klaim

- Pemulihan eksak men-decode informasi yang benar-benar dikirim; bukan menebak file sembarang dari hint kecil.
- TCP localhost adalah antarmuka simulator klasik, bukan koneksi quantum fisik.
- Akses state global adalah diagnostik khusus, bukan pengukuran fisik lokal.
- Checksum bukan enkripsi atau autentikasi.
- Pesan berulang menguji keterulangan, bukan generalisasi model bahasa.
- Sampel terbatas tidak membuktikan teorema atau menjamin kinerja mendatang.
- QML, rekonstruksi pre-shared key, jaringan quantum hardware, dan FTL di luar cakupan rilis ini.

Referensi primer tercantum pada [references.bib](references.bib).
