# Unlock Arsip (Android)

Hapus password dari file .zip/.rar otomatis berdasarkan file .txt
berisi passwordnya. Dibangun jadi .apk lewat GitHub Actions (gratis),
TANPA perlu install Android Studio sama sekali.

## Status pengujian (jujur)

- `core.py` (logika ekstrak, cari password, bungkus ulang, ganti arsip
  lama): **sudah diuji langsung dan terbukti jalan** (berbagai skenario
  sukses maupun gagal).
- `main.py` (tampilan Kivy + izin penyimpanan Android): ditulis sesuai
  pola baku komunitas Kivy, **belum pernah saya jalankan nyata** karena
  sandbox saya tidak bisa install Kivy maupun build Android. Kemungkinan
  besar jalan, tapi kalau ada error pas dicoba di HP, kirim pesan
  errornya ke saya untuk diperbaiki.

## Cara build APK (lewat GitHub, di HP pun bisa)

1. Buat akun GitHub kalau belum punya (gratis): https://github.com/signup
2. Buat repository baru (New repository), beri nama bebas misalnya
   `unlock-arsip`, biarkan "Public", lalu klik "Create repository".
3. Di halaman repo kosong tadi, klik "uploading an existing file", lalu
   drag & drop SEMUA isi folder ini (termasuk folder `.github` dan
   isinya) ke situ. Kalau file `.github/workflows/build-apk.yml` tidak
   ikut ter-upload karena browser tidak mendukung upload folder
   tersembunyi, buat manual lewat "Add file > Create new file", ketik
   nama path-nya persis `.github/workflows/build-apk.yml`, lalu
   copy-paste isinya.
4. Commit (klik "Commit changes").
5. Buka tab "Actions" di repo tersebut. Akan ada proses "Build APK"
   berjalan otomatis (ikon kuning berputar). Tunggu sekitar 20-40 menit
   (build pertama paling lama karena download Android SDK/NDK).
6. Kalau sudah selesai (ikon centang hijau), klik proses tersebut, lalu
   di bagian bawah halaman ada "Artifacts" -> unduh `unlock-arsip-apk`
   (berupa file .zip berisi .apk di dalamnya).
7. Di HP, extract/ekstrak zip itu, lalu install file `.apk`-nya (perlu
   mengizinkan "Install dari sumber tidak dikenal" di pengaturan HP
   untuk browser/file manager yang dipakai).

## Cara pakai aplikasinya setelah terinstall

1. Buka app "Unlock Arsip". Pertama kali buka akan muncul minta izin
   akses penyimpanan — izinkan ("Allow access to manage all files").
2. Taruh file arsip .zip/.rar beserta file .txt berisi passwordnya
   (nama sama, mis. `rahasia.zip` + `rahasia.txt`) di folder yang sama,
   misalnya di folder Download.
3. Di app, isi/pilih folder tersebut, lalu tekan "Proses". Arsip yang
   ketemu password-nya akan otomatis diekstrak dan dibungkus ulang
   tanpa password, menggantikan arsip lama.

Format file password sama seperti versi desktop:
- `<nama_arsip>.txt` di folder yang sama -> prioritas pertama.
- `password.txt` berisi baris `nama_file.zip:password` -> password
  per-file.
- `password.txt` berisi satu baris password saja -> dipakai untuk
  semua arsip yang tidak punya `.txt` sendiri.

## Keterbatasan

- File **.rar** hasil akhirnya akan berbentuk **.zip** baru (Python
  tidak bisa menulis ulang format .rar).
- ZIP terenkripsi **AES** (bukan ZipCrypto lama) butuh pustaka
  `pyzipper` — tambahkan `pyzipper` ke baris `requirements` di
  `buildozer.spec` lalu build ulang kalau arsipmu pakai itu.
- Izin "All files access" di Android 11+ harus diaktifkan manual sekali
  lewat halaman pengaturan yang terbuka otomatis saat app pertama kali
  dibuka.

## Alternatif yang sudah pasti jalan hari ini juga

Kalau proses build/APK ini merepotkan atau gagal, cara paling cepat
yang sudah pasti bisa dipakai di Android **hari ini juga tanpa build
apa pun**: install app **Termux** dari F-Droid, lalu jalankan skrip
desktop (`unlock_arsip.py`, versi CLI) langsung di situ dengan Python.
Tinggal minta saya siapkan versinya kalau mau jalur ini.
